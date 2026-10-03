"""Microphone capture.

The PortAudio callback does the bare minimum: it copies the incoming block
into a bounded queue. Mixing to mono, resampling to 16 kHz and voice
activity detection happen in a worker thread (see ``app.workers``).
"""

from __future__ import annotations

import logging
import queue
import sys
import threading
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)

TARGET_RATE = 16000
# The capture queue holds raw blocks waiting for the VAD worker. The worker
# is much faster than real time, so the queue normally holds a block or two.
# The bound only matters if the worker stalls; blocks are then dropped and
# counted instead of growing memory without limit.
CAPTURE_QUEUE_BLOCKS = 1024


class AudioError(Exception):
    """A microphone problem. ``code`` selects the localized message."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class InputDevice:
    index: int
    name: str
    is_default: bool


def _sounddevice():
    try:
        import sounddevice

        return sounddevice
    except Exception as exc:  # PortAudio library missing or broken
        raise AudioError("audio_backend_unavailable", str(exc)) from exc


def _preferred_host_api(sd) -> int | None:
    """Pick one host API so every physical device is listed exactly once.

    On Windows PortAudio exposes each microphone through MME, DirectSound,
    WASAPI and WDM-KS. WASAPI reports untruncated device names and is the
    modern API, so it is preferred.
    """
    try:
        apis = sd.query_hostapis()
    except Exception:
        return None
    if sys.platform == "win32":
        for index, api in enumerate(apis):
            if "WASAPI" in api.get("name", ""):
                return index
    try:
        return sd.default.hostapi
    except Exception:
        return None


def list_input_devices(refresh: bool = False) -> list[InputDevice]:
    """Return the available microphones.

    ``refresh`` re-initialises PortAudio so newly connected devices appear.
    It must not be used while a stream is open.
    """
    sd = _sounddevice()
    if refresh:
        try:
            sd._terminate()
            sd._initialize()
        except Exception:
            log.exception("Could not refresh the audio device list")
    try:
        devices = sd.query_devices()
        host_api = _preferred_host_api(sd)
        default_index = -1
        if host_api is not None:
            default_index = sd.query_hostapis(host_api).get("default_input_device", -1)
    except Exception as exc:
        raise AudioError("audio_backend_unavailable", str(exc)) from exc

    result = []
    for index, device in enumerate(devices):
        if device.get("max_input_channels", 0) < 1:
            continue
        if host_api is not None and device.get("hostapi") != host_api:
            continue
        result.append(InputDevice(index, device["name"], index == default_index))
    return result


def resolve_device(name: str) -> InputDevice:
    """Find the device to record from.

    An empty name selects the system default. A saved name that no longer
    exists also falls back to the default, so an unplugged headset does not
    block recording.
    """
    devices = list_input_devices()
    if not devices:
        raise AudioError("no_microphone")
    if name:
        for device in devices:
            if device.name == name:
                return device
        log.warning("Saved microphone is not available, using the default device")
    for device in devices:
        if device.is_default:
            return device
    return devices[0]


class Resampler:
    """Streaming conversion of mono audio to 16 kHz.

    A windowed-sinc low-pass filter removes content above the new Nyquist
    frequency, then the signal is sampled at the target rate by linear
    interpolation. Filter and phase state carry over between blocks.
    """

    TAPS = 63

    def __init__(self, source_rate: int) -> None:
        self.source_rate = int(source_rate)
        self._step = self.source_rate / TARGET_RATE
        cutoff = 0.45 * min(TARGET_RATE, self.source_rate) / self.source_rate
        n = np.arange(self.TAPS) - (self.TAPS - 1) / 2
        kernel = 2 * cutoff * np.sinc(2 * cutoff * n) * np.hamming(self.TAPS)
        self._kernel = (kernel / kernel.sum()).astype(np.float32)
        self._history = np.zeros(self.TAPS - 1, dtype=np.float32)
        self._carry = np.zeros(1, dtype=np.float32)  # last filtered sample
        self._phase = 1.0  # read position relative to ``_carry``

    def process(self, block: np.ndarray) -> np.ndarray:
        if self.source_rate == TARGET_RATE:
            return block
        if block.size == 0:
            return block
        padded = np.concatenate((self._history, block))
        filtered = np.convolve(padded, self._kernel, mode="valid").astype(np.float32)
        self._history = padded[-(self.TAPS - 1) :]

        line = np.concatenate((self._carry, filtered))
        last = len(line) - 1
        count = int(np.floor((last - self._phase) / self._step)) + 1 if last >= self._phase else 0
        positions = self._phase + self._step * np.arange(max(count, 0))
        output = np.interp(positions, np.arange(len(line)), line).astype(np.float32)
        self._phase = self._phase + self._step * max(count, 0) - last
        self._carry = line[-1:]
        return output


class AudioRecorder:
    """Owns the microphone stream for one recording session."""

    def __init__(self, device_name: str, blocks: "queue.Queue[np.ndarray]") -> None:
        self._device_name = device_name
        self._blocks = blocks
        self._stream = None
        self._lock = threading.Lock()
        self.device: InputDevice | None = None
        self.sample_rate = TARGET_RATE
        self.dropped_blocks = 0
        self.overflows = 0
        # Set when PortAudio ends the stream on its own (device unplugged).
        self.aborted = threading.Event()
        self._closing = False

    def start(self) -> None:
        """Open the microphone. Raises :class:`AudioError` on failure."""
        sd = _sounddevice()
        self.device = resolve_device(self._device_name)
        info = sd.query_devices(self.device.index)
        channels = max(1, min(2, int(info.get("max_input_channels", 1))))
        native_rate = int(info.get("default_samplerate") or TARGET_RATE)

        extra = None
        try:
            if "WASAPI" in sd.query_hostapis(info["hostapi"]).get("name", ""):
                extra = sd.WasapiSettings(auto_convert=True)
        except Exception:
            extra = None

        # Prefer 16 kHz straight from the driver; otherwise capture at the
        # device's own rate and resample in software.
        attempts = [(TARGET_RATE, extra), (native_rate, extra), (native_rate, None)]
        last_error: Exception | None = None
        for rate, settings in attempts:
            try:
                stream = sd.InputStream(
                    device=self.device.index,
                    samplerate=rate,
                    channels=channels,
                    dtype="float32",
                    blocksize=0,
                    callback=self._callback,
                    finished_callback=self._finished,
                    extra_settings=settings,
                )
                stream.start()
            except Exception as exc:
                last_error = exc
                log.info("Opening microphone at %d Hz failed: %s", rate, exc)
                continue
            with self._lock:
                self._stream = stream
            self.sample_rate = rate
            log.info(
                "Microphone opened: %d Hz, %d channel(s), device index %d",
                rate,
                channels,
                self.device.index,
            )
            return
        raise AudioError("microphone_open_failed", str(last_error))

    def stop(self) -> None:
        """Stop capturing and release the device. Queued audio is kept."""
        with self._lock:
            stream, self._stream = self._stream, None
            self._closing = True
        if stream is None:
            return
        try:
            stream.stop()
        except Exception:
            log.exception("Stopping the microphone stream failed")
        try:
            stream.close()
        except Exception:
            log.exception("Closing the microphone stream failed")
        log.info(
            "Microphone released (dropped blocks: %d, driver overflows: %d)",
            self.dropped_blocks,
            self.overflows,
        )

    def _callback(self, indata, frames, time_info, status) -> None:
        if status and status.input_overflow:
            self.overflows += 1
        block = indata.mean(axis=1) if indata.shape[1] > 1 else indata[:, 0].copy()
        try:
            self._blocks.put_nowait(block)
        except queue.Full:
            self.dropped_blocks += 1

    def _finished(self) -> None:
        if not self._closing:
            self.aborted.set()
