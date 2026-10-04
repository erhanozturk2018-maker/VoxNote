"""VoxNote - local speech recorder and transcription desktop application."""

APP_NAME = "VoxNote"
APP_VERSION = "0.5.1"

# Whisper models the user can choose from, with their approximate download
# size in megabytes. Names are faster-whisper model identifiers.
MODELS = {
    "small": 500,
    "medium": 1500,
    "large-v3-turbo": 1600,
    "large-v3": 3100,
}
DEFAULT_MODEL = "large-v3-turbo"
