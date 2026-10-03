# Export Formats

VoxNote can save a session as Markdown, plain text, JSON, Microsoft Word or
PDF. All formats are produced from the same internal document, so they
contain the same information.

- [Common rules](#common-rules)
- [Content options](#content-options)
- [Metadata](#metadata)
- [Markdown](#markdown-md)
- [Plain text](#plain-text-txt)
- [JSON](#json-json)
- [Microsoft Word](#microsoft-word-docx)
- [PDF](#pdf-pdf)
- [Adding a format](#adding-a-format)

## Common rules

- **The transcript is not modified.** Content options decide how the text is
  arranged and what accompanies it, never the words. The text of every segment is exactly
  what the recogniser returned, apart from leading and trailing spaces. There
  is no spelling or grammar correction and no translation.
- **Language information is kept separate from the text.** Languages appear
  as headings (documents) or as fields (JSON), never inside the transcript
  text.
- **Segments are in the order they were spoken.** Consecutive segments in the
  same language are grouped under one language heading.
- **Timestamps** are the start of each segment, measured from the beginning
  of the recording, in the form `[HH:MM:SS]`. They can be switched off for
  Markdown, text, Word and PDF in **Settings › General**. JSON always
  contains start and end times.
- **Headings and labels are in English** in every export, regardless of the
  interface language, so that files are consistent and easy to process.
- **Encoding** is UTF-8 without a byte order mark for Markdown, text and
  JSON. Line endings are `LF`.
- **Characters that a format cannot represent** are handled as follows:
  control characters (other than tab and line break) are removed from Word
  and PDF output because those formats cannot store them. Markdown, text and
  JSON keep the text byte for byte. Transcript text is not escaped in
  Markdown; in the unlikely case that it contains Markdown syntax, a viewer
  will interpret it.
- **Files are written safely.** Content is written to a temporary file and
  moved into place only when complete, so an interrupted export never leaves
  a half-written document. Automatic saving never overwrites an existing
  file; it appends `_2`, `_3`, … to the name.

## Content options

The user can choose what Markdown, text, Word and PDF documents contain
(**Document Content** in the main window). The options are described by
`ExportOptions` in `app/exporters/base.py`:

| Option | Values | Default | Effect |
| --- | --- | --- | --- |
| `layout` | `lines`, `paragraph` | `lines` | One entry per recognised sentence, or the whole transcript joined with single spaces into one paragraph |
| `include_timestamps` | on, off | on | `[HH:MM:SS]` before each line (`lines` only) |
| `language_headings` | on, off | on | A heading whenever the language changes (`lines` only) |
| `headings` | on, off | on | The title and the "Transcript" heading |
| `metadata` | any subset of `date`, `languages`, `duration`, `session_id`, `model` | all | Which metadata rows are written; their order is fixed |

With `layout = paragraph`, `headings` off and no metadata, a plain text file
contains exactly the transcript as one paragraph and nothing else.

The examples below show the default options. **JSON is not affected by these
options**: it always contains the complete session.

## Metadata

| Field | Example | Meaning |
| --- | --- | --- |
| Date | `2026-10-03 14:30:00` | Local date and time at which the recording started |
| Languages | `English, Turkish` | Distinct languages of the session, ordered by first confident detection; `None detected` for an empty session |
| Duration | `00:05:24` | Length of the recording, including silence |
| Session ID | `3f9a1c2e` | Random identifier of the session |
| Model | `Whisper large-v3-turbo (faster-whisper)` | Speech model that produced the transcript |

JSON additionally records the UTC offset of the start time, the language
codes, and the device and number format the model ran on.

## Markdown (`.md`)

```markdown
# Speaking Session

- Date: 2026-10-03 14:30:00
- Languages: English, Turkish
- Duration: 00:05:24
- Session ID: 3f9a1c2e
- Model: Whisper large-v3-turbo (faster-whisper)

## Transcript

### English

[00:00:02] Yesterday I went to the gym.

[00:00:06] After that I was really tired.

### Turkish

[00:00:10] Sonra arkadaşımı gördüm.

### English

[00:00:18] We talked for a while.
```

Each segment is its own paragraph. A session without speech contains
`_No speech was detected in this session._` below the Transcript heading.
(VoxNote does not save such sessions automatically; this text only appears
when an exporter is called for an empty session.)

## Plain text (`.txt`)

```text
Speaking Session
================

Date: 2026-10-03 14:30:00
Languages: English, Turkish
Duration: 00:05:24
Session ID: 3f9a1c2e
Model: Whisper large-v3-turbo (faster-whisper)

Transcript
----------

[English]
[00:00:02] Yesterday I went to the gym.
[00:00:06] After that I was really tired.

[Turkish]
[00:00:10] Sonra arkadaşımı gördüm.

[English]
[00:00:18] We talked for a while.
```

## JSON (`.json`)

```json
{
  "schema_version": 1,
  "application": {
    "name": "VoxNote",
    "version": "0.4.0"
  },
  "session": {
    "id": "3f9a1c2e",
    "started_at": "2026-10-03T14:30:00+03:00",
    "duration_seconds": 324.0,
    "languages": ["en", "tr"],
    "language_names": ["English", "Turkish"],
    "model": "large-v3-turbo",
    "device": "cuda",
    "compute_type": "float16"
  },
  "segments": [
    {
      "index": 0,
      "start": 2.0,
      "end": 5.4,
      "language": "en",
      "language_probability": 0.98,
      "text": "Yesterday I went to the gym."
    },
    {
      "index": 1,
      "start": 10.2,
      "end": 13.6,
      "language": "tr",
      "language_probability": 0.97,
      "text": "Sonra arkadaşımı gördüm."
    }
  ]
}
```

(The file is written with one array element per line; arrays are shown
compactly here.)

### Schema, version 1

Top level:

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | integer | Version of this schema. Currently `1`. |
| `application` | object | Program that wrote the file. |
| `session` | object | Metadata of the recording. |
| `segments` | array of objects | Transcript, in chronological order. May be empty. |

`application`:

| Field | Type | Description |
| --- | --- | --- |
| `name` | string | Always `VoxNote`. |
| `version` | string | Application version. |

`session`:

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Random session identifier (8 hexadecimal characters). |
| `started_at` | string | ISO 8601 local date and time with UTC offset. |
| `duration_seconds` | number | Length of the recording in seconds, including silence. Not negative. |
| `languages` | array of strings | Distinct language codes as used by Whisper (for example `en`, `tr`), ordered by first confident detection. |
| `language_names` | array of strings | English names for `languages`, in the same order. |
| `model` | string | Name of the Whisper model: `small`, `medium` or `large-v3-turbo`. |
| `device` | string | `cuda` or `cpu`. May be empty for a recovered session. |
| `compute_type` | string | Number format used for inference, for example `float16` or `int8`. May be empty. |

Each element of `segments`:

| Field | Type | Description |
| --- | --- | --- |
| `index` | integer | Position in the array, starting at 0. |
| `start` | number | Start in seconds from the beginning of the recording. |
| `end` | number | End in seconds. Never smaller than `start`. |
| `language` | string | Language code the segment was transcribed in. |
| `language_probability` | number | Model's probability (0 to 1) for that language, for the utterance the segment belongs to. |
| `text` | string | Recognised text. Never empty. |

Notes:

- One spoken utterance can produce several segments (the recogniser splits
  longer utterances into sentences). They share the same `language` and
  `language_probability`.
- Times are rounded to two decimals, probabilities to four.
- Segment times come from the recogniser and are approximate.

### Versioning policy

`schema_version` is increased whenever a field is removed, renamed, or
changes its type or meaning. Adding a new optional field does not change the
version; readers should ignore fields they do not know.

The function `validate_json_document` in `app/exporters/json_exporter.py`
checks a document against this schema and is used by the tests.

## Microsoft Word (`.docx`)

- Title "Speaking Session", a bulleted list with the metadata, a "Transcript"
  heading, one sub-heading per language block and one paragraph per segment.
- Uses the default styles of a new Word document, so it adopts your template
  when you paste it elsewhere.
- The document properties contain the title and the session start as creation
  date. The author field is empty.
- Written with python-docx. All Unicode text is supported; the fonts used for
  display are chosen by the word processor.

## PDF (`.pdf`)

- A4 pages with 20 mm margins, the same structure as the Word document.
- **Fonts.** The standard PDF fonts cannot display characters such as
  `ğ ş ı İ`. VoxNote therefore embeds a Unicode TrueType font from the
  operating system. On Windows the candidates are, in this order: Segoe UI,
  Arial, Tahoma, then Microsoft YaHei, Yu Gothic, MS Gothic, Malgun Gothic,
  Nirmala UI, Leelawadee UI, Ebrima and Segoe UI Symbol for other scripts.
  For every paragraph, the first font that contains all of its characters is
  used, so one document can mix scripts. Only the characters actually used
  are embedded, and the PDF displays the same on computers that lack the font.
- If no usable font exists, the export fails with a clear message and no file
  is created, rather than producing a PDF with wrong characters.
- To force a specific font, set the environment variable `VOXNOTE_PDF_FONT`
  to the path of a `.ttf` file before starting VoxNote.
- **Limitation:** right-to-left scripts (Arabic, Hebrew) and scripts that
  need complex shaping (for example Devanagari) are not rendered correctly.
  Use another format for these languages.
- Written with ReportLab.

## Adding a format

1. Create `app/exporters/<name>_exporter.py` with a subclass of `Exporter`
   (`app/exporters/base.py`). Set `format_id`, `extension` and `label`, and
   implement `write(session, path, options)`. Use `build_document(session,
   options)` to get the metadata and language blocks.
2. Add an instance to `EXPORTERS` in `app/exporters/__init__.py`.
3. Add the identifier to `EXPORT_FORMATS` in `app/settings_manager.py`.

The format then appears in the main window, in Settings and in the Save As
dialog. Nothing in the recording or recognition code needs to change.
