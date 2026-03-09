"""
xrylib.report — High-level XRYReport class.

XRYReport is the primary entry point for end-users.  It wraps the low-level
XRYParser and extractors to expose typed, model-backed collections of every
forensic artifact category found in a .xry file.

Usage
-----
    from xrylib import XRYReport

    report = XRYReport("dump.xry")

    print(report.device)
    for call in report.calls:
        print(call.direction, call.number, call.timestamp)
    for msg in report.messages:
        if msg.deleted:
            print("[RECOVERED]", msg.body)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .extractors import CATEGORY_EXTRACTOR, extract_device_info
from .models import (
    BrowserHistory,
    CalendarEvent,
    Call,
    ChatMessage,
    Contact,
    DeviceInfo,
    Email,
    InstalledApp,
    Location,
    MediaFile,
    Message,
    Note,
    UserAccount,
    WirelessNetwork,
)
from .parser import XRYParser


class XRYReport:
    """
    A parsed XRY forensic report.

    All artifact collections are lazy-loaded on first access and then cached.

    Parameters
    ----------
    path : str | Path
        Path to the .xry XML file.
    strict : bool
        Passed through to XRYParser — if True, unrecognised item types raise
        an exception instead of being silently skipped.

    Attributes
    ----------
    device      : DeviceInfo
    contacts    : List[Contact]
    calls       : List[Call]
    messages    : List[Message]
    chat_messages: List[ChatMessage]
    emails      : List[Email]
    media_files : List[MediaFile]
    locations   : List[Location]
    browser_history: List[BrowserHistory]
    installed_apps : List[InstalledApp]
    notes       : List[Note]
    calendar_events: List[CalendarEvent]
    wireless_networks: List[WirelessNetwork]
    user_accounts: List[UserAccount]
    unknown_items: List[Dict[str, Any]]   — items whose type was not recognised
    """

    def __init__(self, path: str | Path, strict: bool = False):
        self.path = Path(path)
        self._parser = XRYParser(str(self.path), strict=strict)
        self._parser.load()
        self._cache: Dict[str, List] = {}
        self._all_items: Optional[Dict[str, List[Dict]]] = None

    # ------------------------------------------------------------------ #
    #  Internal: load & cache all raw items once                           #
    # ------------------------------------------------------------------ #

    def _ensure_loaded(self) -> None:
        if self._all_items is None:
            self._all_items = self._parser.items_by_category()

    def _get(self, category: str) -> List:
        if category not in self._cache:
            self._ensure_loaded()
            extractor = CATEGORY_EXTRACTOR.get(category)
            raw_list = self._all_items.get(category, [])
            if extractor:
                self._cache[category] = [extractor(f) for f in raw_list]
            else:
                self._cache[category] = raw_list
        return self._cache[category]

    # ------------------------------------------------------------------ #
    #  Device metadata                                                     #
    # ------------------------------------------------------------------ #

    @property
    def device(self) -> DeviceInfo:
        """Device and extraction metadata."""
        if "_device" not in self._cache:
            self._cache["_device"] = extract_device_info(self._parser.extraction_info)
        return self._cache["_device"]

    @property
    def xry_version(self) -> Optional[str]:
        """XRY file format version."""
        return self._parser.version

    # ------------------------------------------------------------------ #
    #  Artifact collections                                                #
    # ------------------------------------------------------------------ #

    @property
    def contacts(self) -> List[Contact]:
        """Address-book entries."""
        return self._get("contacts")

    @property
    def calls(self) -> List[Call]:
        """Call log records."""
        return self._get("calls")

    @property
    def messages(self) -> List[Message]:
        """SMS and MMS messages."""
        return self._get("messages")

    @property
    def chat_messages(self) -> List[ChatMessage]:
        """Instant messages from third-party chat apps."""
        return self._get("chat_messages")

    @property
    def emails(self) -> List[Email]:
        """E-mail messages."""
        return self._get("emails")

    @property
    def media_files(self) -> List[MediaFile]:
        """Images, videos, and audio files."""
        return self._get("media_files")

    @property
    def locations(self) -> List[Location]:
        """GPS and network location records."""
        return self._get("locations")

    @property
    def browser_history(self) -> List[BrowserHistory]:
        """Web browser history, bookmarks, and cookies."""
        return self._get("browser_history")

    @property
    def installed_apps(self) -> List[InstalledApp]:
        """Installed application records."""
        return self._get("installed_apps")

    @property
    def notes(self) -> List[Note]:
        """Notes and memos."""
        return self._get("notes")

    @property
    def calendar_events(self) -> List[CalendarEvent]:
        """Calendar / agenda events."""
        return self._get("calendar_events")

    @property
    def wireless_networks(self) -> List[WirelessNetwork]:
        """Wi-Fi networks the device has seen or connected to."""
        return self._get("wireless_networks")

    @property
    def user_accounts(self) -> List[UserAccount]:
        """Online accounts and stored credentials."""
        return self._get("user_accounts")

    @property
    def unknown_items(self) -> List[Dict[str, Any]]:
        """Raw field dicts for items whose type was not recognised."""
        self._ensure_loaded()
        return self._all_items.get("unknown", [])

    # ------------------------------------------------------------------ #
    #  Convenience / query helpers                                         #
    # ------------------------------------------------------------------ #

    def search_messages(self, keyword: str, case_sensitive: bool = False) -> List[Message]:
        """Return all messages whose body contains *keyword*."""
        kw = keyword if case_sensitive else keyword.lower()
        result = []
        for msg in self.messages:
            body = msg.body or ""
            if not case_sensitive:
                body = body.lower()
            if kw in body:
                result.append(msg)
        return result

    def search_chat_messages(self, keyword: str, case_sensitive: bool = False) -> List[ChatMessage]:
        """Return all chat messages whose body contains *keyword*."""
        kw = keyword if case_sensitive else keyword.lower()
        result = []
        for msg in self.chat_messages:
            body = msg.body or ""
            if not case_sensitive:
                body = body.lower()
            if kw in body:
                result.append(msg)
        return result

    def deleted_items(self, category: str) -> List:
        """Return only deleted (recovered) items from a given category."""
        return [item for item in self._get(category) if getattr(item, "deleted", False)]

    def contacts_by_name(self, name: str, case_sensitive: bool = False) -> List[Contact]:
        """Look up contacts whose name matches (substring)."""
        target = name if case_sensitive else name.lower()
        result = []
        for c in self.contacts:
            cn = (c.name or "") if case_sensitive else (c.name or "").lower()
            if target in cn:
                result.append(c)
        return result

    def calls_from_number(self, number: str) -> List[Call]:
        """Return all calls involving a specific phone number."""
        return [c for c in self.calls if (c.number or "") == number]

    def locations_with_gps(self) -> List[Location]:
        """Return only locations that have valid lat/lon coordinates."""
        return [loc for loc in self.locations if loc.coordinates is not None]

    # ------------------------------------------------------------------ #
    #  Summary / stats                                                     #
    # ------------------------------------------------------------------ #

    def summary(self) -> Dict[str, Any]:
        """Return a dict summarising the counts of all artifact categories."""
        return {
            "file": str(self.path),
            "xry_version": self.xry_version,
            "device": self.device.device_name,
            "imei": self.device.imei,
            "extraction_date": (
                self.device.extraction_date.isoformat()
                if self.device.extraction_date else None
            ),
            "counts": {
                "contacts": len(self.contacts),
                "calls": len(self.calls),
                "messages": len(self.messages),
                "chat_messages": len(self.chat_messages),
                "emails": len(self.emails),
                "media_files": len(self.media_files),
                "locations": len(self.locations),
                "browser_history": len(self.browser_history),
                "installed_apps": len(self.installed_apps),
                "notes": len(self.notes),
                "calendar_events": len(self.calendar_events),
                "wireless_networks": len(self.wireless_networks),
                "user_accounts": len(self.user_accounts),
                "unknown_items": len(self.unknown_items),
            },
        }

    def summary_json(self, indent: int = 2) -> str:
        """Return the summary as a formatted JSON string."""
        return json.dumps(self.summary(), indent=indent, default=str)

    # ------------------------------------------------------------------ #
    #  Export helpers                                                      #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """
        Export the entire report as a nested dict.

        Warning: this materialises all artifact collections; use selectively
        for large extractions.
        """
        return {
            "device": self.device.to_dict(),
            "contacts": [c.to_dict() for c in self.contacts],
            "calls": [c.to_dict() for c in self.calls],
            "messages": [m.to_dict() for m in self.messages],
            "chat_messages": [m.to_dict() for m in self.chat_messages],
            "emails": [e.to_dict() for e in self.emails],
            "media_files": [f.to_dict() for f in self.media_files],
            "locations": [loc.to_dict() for loc in self.locations],
            "browser_history": [b.to_dict() for b in self.browser_history],
            "installed_apps": [a.to_dict() for a in self.installed_apps],
            "notes": [n.to_dict() for n in self.notes],
            "calendar_events": [e.to_dict() for e in self.calendar_events],
            "wireless_networks": [w.to_dict() for w in self.wireless_networks],
            "user_accounts": [u.to_dict() for u in self.user_accounts],
        }

    def to_json(self, indent: int = 2) -> str:
        """Export the entire report as a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def iter_all_artifacts(self) -> Iterator:
        """Iterate over every extracted artifact in all categories."""
        for category in CATEGORY_EXTRACTOR:
            yield from self._get(category)

    # ------------------------------------------------------------------ #
    #  Dunder                                                              #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        s = self.summary()
        counts = s.get("counts", {})
        total = sum(counts.values())
        return (
            f"XRYReport(file={self.path.name!r}, "
            f"device={s.get('device')!r}, "
            f"total_artifacts={total})"
        )
