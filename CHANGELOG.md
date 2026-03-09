# Changelog

All notable changes to **xrylib** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2024-07-01 — "First Light"

Initial release.

### Added — Artifact Categories (14)

- `DeviceInfo` — Device identity, hardware, OS, extraction metadata, case info
- `Contact` — Address-book entries with typed phone numbers and e-mail addresses
- `Call` — Call log records (voice, video, VoIP) with formatted duration
- `Message` — SMS and MMS messages with attachment support
- `ChatMessage` — Instant messages from WhatsApp, Telegram, Signal, etc.
- `Email` — E-mail messages from on-device mail clients
- `MediaFile` — Images, videos, audio with full EXIF metadata and GPS coordinates
- `Location` — GPS and network location records
- `BrowserHistory` — History, bookmarks, downloads, cookies, form data
- `InstalledApp` — Installed applications with permissions and metadata
- `Note` — Notes and memos
- `CalendarEvent` — Calendar and agenda events with recurrence and attendees
- `WirelessNetwork` — Wi-Fi networks the device has seen or connected to
- `UserAccount` — Online accounts and stored credentials

### Added — Core Architecture

- `XRYParser` — Low-level XML → raw dict parser with gzip transparent decompression
- `XRYReport` — High-level facade with lazy-loaded, cached artifact collections
- `ForensicArtifact` base class — `raw_fields`, `deleted`, `to_dict()`, `to_json()`, `get_field()`
- Custom exception hierarchy: `XRYError`, `XRYFileNotFoundError`, `XRYParseError`,
  `XRYUnsupportedVersionError`, `XRYExtractionError`
- Utility helpers: `parse_datetime()`, `parse_bool()`, `normalise_phone()`,
  `parse_direction()`, `parse_coordinates()`

### Added — Query Helpers on `XRYReport`

- `search_messages(keyword)` — full-text search across SMS/MMS bodies
- `search_chat_messages(keyword)` — full-text search across chat message bodies
- `deleted_items(category)` — filter recovered/deleted artifacts by category
- `contacts_by_name(name)` — substring name lookup
- `calls_from_number(number)` — filter calls by phone number
- `locations_with_gps()` — filter locations with valid lat/lon coordinates
- `iter_all_artifacts()` — iterate every artifact across all categories
- `summary()` / `summary_json()` — artifact count report
- `to_dict()` / `to_json()` — full report export

### Added — Test Suite

- 37 unit tests covering utilities, parser, and all 14 artifact models
- 36/37 passing on first release (1 skipped: pytest `tmp_path` fixture behaviour)

### Technical Notes

- Zero external dependencies — stdlib only
- Python 3.8+ compatible
- gzip-compressed `.xry` files transparently supported
- `strict=True` mode raises on unsupported XRY versions
