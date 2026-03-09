"""
xrylib.parser — Low-level XML parser for .xry forensic report files.

XRY exports XML in a structure similar to:

    <xry version="9.3">
      <extractioninfo>
        <devicename>Samsung Galaxy S21</devicename>
        <imei>123456789012345</imei>
        ...
      </extractioninfo>
      <data>
        <item type="Contact" deleted="false" id="42" source="Contacts/Phone">
          <field name="Name">John Doe</field>
          <field name="Phone" phonetype="Mobile">+441234567890</field>
          ...
        </item>
        <item type="SMS" ...>
          ...
        </item>
        ...
      </data>
    </xry>

The parser returns a dict-based intermediate representation which the
higher-level XRYReport class turns into typed model objects.
"""

from __future__ import annotations

import gzip
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .exceptions import XRYFileNotFoundError, XRYParseError, XRYUnsupportedVersionError

# Minimum supported XRY XML version (we accept 7.x and above)
_MIN_VERSION = 7
_MAX_VERSION = 99  # future-proof

# Known XRY item type strings → internal category keys
ITEM_TYPE_MAP: Dict[str, str] = {
    # Contacts
    "contact": "contacts",
    "contacts": "contacts",
    "phonebook": "contacts",
    # Calls
    "call": "calls",
    "calls": "calls",
    "call log": "calls",
    "calllog": "calls",
    # SMS / MMS
    "sms": "messages",
    "mms": "messages",
    "message": "messages",
    "messages": "messages",
    "text message": "messages",
    # Chat
    "chat": "chat_messages",
    "chat message": "chat_messages",
    "instant message": "chat_messages",
    "whatsapp": "chat_messages",
    "telegram": "chat_messages",
    "signal": "chat_messages",
    # Email
    "email": "emails",
    "e-mail": "emails",
    "mail": "emails",
    # Media
    "image": "media_files",
    "photo": "media_files",
    "video": "media_files",
    "audio": "media_files",
    "media": "media_files",
    "file": "media_files",
    # Location
    "location": "locations",
    "gps": "locations",
    "route point": "locations",
    "cell tower": "locations",
    # Browser
    "browser history": "browser_history",
    "visited page": "browser_history",
    "bookmark": "browser_history",
    "cookie": "browser_history",
    "web history": "browser_history",
    # Apps
    "installed application": "installed_apps",
    "application": "installed_apps",
    "app": "installed_apps",
    # Notes
    "note": "notes",
    "memo": "notes",
    # Calendar
    "calendar": "calendar_events",
    "calendar event": "calendar_events",
    "appointment": "calendar_events",
    # Wi-Fi
    "wireless network": "wireless_networks",
    "wifi": "wireless_networks",
    "wi-fi": "wireless_networks",
    "wlan": "wireless_networks",
    "wi-fi network": "wireless_networks",
    "wifi network": "wireless_networks",
    "wireless": "wireless_networks",
    # Accounts
    "user account": "user_accounts",
    "account": "user_accounts",
}


def _resolve_category(type_str: str) -> str:
    """Map an XRY item type string to an internal category key."""
    return ITEM_TYPE_MAP.get(type_str.lower().strip(), "unknown")


class XRYParser:
    """
    Low-level parser for XRY XML report files.

    Parameters
    ----------
    path : str
        Path to the .xry file.
    strict : bool
        If True, raise exceptions on unsupported version or unrecognised
        item types. If False, skip unknowns silently (default: False).
    """

    def __init__(self, path: str, strict: bool = False):
        self.path = path
        self.strict = strict
        self._tree: Optional[ET.ElementTree] = None
        self._root: Optional[ET.Element] = None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def load(self) -> "XRYParser":
        """
        Load and parse the XRY file.

        Returns self for chaining: ``parser = XRYParser(path).load()``.

        Raises
        ------
        XRYFileNotFoundError
            If the file does not exist.
        XRYParseError
            If the file is not valid XML.
        XRYUnsupportedVersionError
            If strict=True and the XRY version is outside the supported range.
        """
        if not os.path.isfile(self.path):
            raise XRYFileNotFoundError(f"File not found: {self.path!r}")

        raw = self._read_file()

        try:
            self._root = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise XRYParseError(f"Failed to parse XML in {self.path!r}: {exc}") from exc

        self._validate_version()
        return self

    @property
    def version(self) -> Optional[str]:
        """XRY file format version string, e.g. '9.3'."""
        if self._root is None:
            return None
        return self._root.get("version")

    @property
    def extraction_info(self) -> Dict[str, str]:
        """
        Flat dict of all fields within the <extractioninfo> block.
        Keys are lower-cased tag names; values are stripped text content.
        """
        if self._root is None:
            return {}
        info_el = self._root.find("extractioninfo")
        if info_el is None:
            # Some versions use <deviceinfo>
            info_el = self._root.find("deviceinfo")
        if info_el is None:
            return {}
        return {child.tag.lower(): (child.text or "").strip() for child in info_el}

    def iter_items(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """
        Iterate over all <item> elements in the <data> block.

        Yields
        ------
        (category, fields)
            category : str
                Internal category key (e.g. 'contacts', 'calls', …).
            fields : dict
                Parsed fields for the item, including special keys:
                    '_type'     — original XRY type attribute
                    '_deleted'  — bool
                    '_id'       — str or None
                    '_source'   — str or None
        """
        if self._root is None:
            return

        data_el = self._root.find("data")
        if data_el is None:
            return

        for item_el in data_el.iter("item"):
            type_attr = item_el.get("type", "")
            category = _resolve_category(type_attr)

            if category == "unknown" and self.strict:
                continue

            fields = self._parse_item_element(item_el)
            fields["_type"] = type_attr
            fields["_deleted"] = item_el.get("deleted", "false").lower() == "true"
            fields["_id"] = item_el.get("id")
            fields["_source"] = item_el.get("source")

            yield category, fields

    def items_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return all items grouped by category.

        Returns
        -------
        dict mapping category → list of field dicts.
        """
        result: Dict[str, List[Dict[str, Any]]] = {}
        for category, fields in self.iter_items():
            result.setdefault(category, []).append(fields)
        return result

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _read_file(self) -> bytes:
        """Read the file, transparently decompressing gzip if needed."""
        with open(self.path, "rb") as fh:
            header = fh.read(2)
            fh.seek(0)
            if header == b"\x1f\x8b":
                with gzip.open(fh) as gz:
                    return gz.read()
            return fh.read()

    def _validate_version(self) -> None:
        """Check XRY version against supported range."""
        v = self.version
        if v is None:
            return
        try:
            major = int(v.split(".")[0])
        except (ValueError, IndexError):
            return
        if major < _MIN_VERSION or major > _MAX_VERSION:
            if self.strict:
                raise XRYUnsupportedVersionError(v)

    def _parse_item_element(self, item_el: ET.Element) -> Dict[str, Any]:
        """
        Parse a single <item> element into a flat dict.

        Handles:
          - <field name="X">value</field>             → fields["X"] = "value"
          - <field name="X" subtype="Y">value</field> → fields["X"] → list of (value, subtype)
          - <field name="X"><subfield name="Y">…
        """
        fields: Dict[str, Any] = {}

        for field_el in item_el:
            tag = field_el.tag.lower()
            if tag != "field":
                continue

            name = field_el.get("name", field_el.get("type", tag))
            value = (field_el.text or "").strip()

            # Collect extra attributes (e.g. phonetype="Mobile")
            extras = {
                k: v
                for k, v in field_el.attrib.items()
                if k.lower() not in ("name", "type")
            }

            # Handle nested <subfield> elements
            subfields = list(field_el)
            if subfields:
                nested: Dict[str, str] = {}
                for sf in subfields:
                    sf_name = sf.get("name", sf.tag)
                    nested[sf_name] = (sf.text or "").strip()
                existing = fields.get(name)
                if existing is None:
                    fields[name] = nested
                elif isinstance(existing, list):
                    existing.append(nested)
                else:
                    fields[name] = [existing, nested]
                continue

            # Merge value + extras into an entry dict if extras exist
            entry: Any
            if extras:
                entry = {"value": value, **extras}
            else:
                entry = value

            existing = fields.get(name)
            if existing is None:
                fields[name] = entry
            elif isinstance(existing, list):
                existing.append(entry)
            else:
                fields[name] = [existing, entry]

        return fields
