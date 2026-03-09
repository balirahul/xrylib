# xrylib

**xrylib** is a Python library for parsing and extracting forensic artifacts from `.xry` files produced by [MSAB XRY](https://www.msab.com/products/xry/), a leading mobile device forensic tool.

---

## Installation

```bash
pip install .          # from source
# or
pip install xrylib     # once published to PyPI
```

No external dependencies — only the Python standard library.

---

## Quick Start

```python
from xrylib import XRYReport

report = XRYReport("extraction.xry")

# Device metadata
print(report.device.device_name)   # e.g. "Samsung Galaxy S21"
print(report.device.imei)

# Iterate contacts
for contact in report.contacts:
    print(contact.name, contact.primary_phone)

# Iterate calls
for call in report.calls:
    print(call.direction, call.number, call.duration_formatted)

# Iterate SMS messages (including deleted)
for msg in report.messages:
    if msg.deleted:
        print("[RECOVERED]", msg.body)

# Search message content
hits = report.search_messages("meet me")

# Chat messages (WhatsApp, Telegram, Signal …)
for cm in report.chat_messages:
    print(f"[{cm.application}] {cm.sender_name}: {cm.body}")

# GPS locations
for loc in report.locations_with_gps():
    print(loc.latitude, loc.longitude, loc.timestamp)

# Export everything to JSON
print(report.to_json())

# Summary statistics
print(report.summary_json())
```

---

## Supported Artifact Categories

| Property | Model Class | Description |
|---|---|---|
| `report.device` | `DeviceInfo` | IMEI, model, OS, examiner, case number |
| `report.contacts` | `Contact` | Phone book entries (phone + SIM) |
| `report.calls` | `Call` | Incoming / outgoing / missed calls |
| `report.messages` | `Message` | SMS and MMS messages |
| `report.chat_messages` | `ChatMessage` | WhatsApp, Telegram, Signal, etc. |
| `report.emails` | `Email` | Emails from device mail clients |
| `report.media_files` | `MediaFile` | Images, videos, audio (with EXIF GPS) |
| `report.locations` | `Location` | GPS / cell / Wi-Fi position records |
| `report.browser_history` | `BrowserHistory` | URLs, bookmarks, cookies |
| `report.installed_apps` | `InstalledApp` | Installed application records |
| `report.notes` | `Note` | Notes and memos |
| `report.calendar_events` | `CalendarEvent` | Calendar / agenda events |
| `report.wireless_networks` | `WirelessNetwork` | Wi-Fi networks (SSID, BSSID, password) |
| `report.user_accounts` | `UserAccount` | Stored online account credentials |

---

## Forensic Features

- **Deleted / recovered artifact detection** — every model exposes a `deleted` boolean flag
- **Lazy loading** — artifact collections are parsed on first access and cached
- **Raw field access** — every model exposes `raw_fields` for full transparency
- **gzip support** — transparently decompresses gzip-compressed `.xry` files
- **Strict mode** — `XRYReport(path, strict=True)` raises on unsupported XRY versions
- **JSON export** — `report.to_json()`, `artifact.to_json()`, `report.summary_json()`
- **Query helpers** — `search_messages()`, `contacts_by_name()`, `deleted_items()`, `locations_with_gps()`

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Running the Demo

```bash
python examples/demo.py
```

---

## Architecture

```
xrylib/
├── __init__.py          # Public API surface
├── parser.py            # Low-level XML → raw dict parser (XRYParser)
├── report.py            # High-level facade (XRYReport)
├── exceptions.py        # Custom exception hierarchy
├── models/
│   └── __init__.py      # Typed dataclass models for every artifact
├── extractors/
│   └── __init__.py      # Field-dict → model conversion functions
└── utils/
    └── __init__.py      # Date parsing, normalisation, coercion helpers
```

---

## Comparison with ufedlib-py

| Feature | xrylib | ufedlib-py |
|---|---|---|
| Source format | MSAB XRY XML | Cellebrite UFED XML/XLSX |
| Typed models | ✅ | ✅ |
| Deleted item flag | ✅ | ✅ |
| JSON export | ✅ | Partial |
| Zero dependencies | ✅ | ✅ |
| gzip support | ✅ | — |

---

## License

MIT
