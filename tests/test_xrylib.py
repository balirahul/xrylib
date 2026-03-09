"""
tests/test_xrylib.py — Unit tests for xrylib.

Run with:  python -m pytest tests/ -v
"""

import sys
import os
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from xrylib import XRYReport, XRYParser
from xrylib.models import Contact, Call, Message, Location, MediaFile
from xrylib.utils import (
    parse_datetime,
    parse_bool,
    parse_int,
    parse_float,
    normalise_phone,
    parse_direction,
    parse_coordinates,
)
from xrylib.exceptions import XRYFileNotFoundError, XRYParseError

# ======================================================================== #
#  Fixtures — build minimal XRY XML strings                                #
# ======================================================================== #

MINIMAL_XRY = """<?xml version="1.0" encoding="UTF-8"?>
<xry version="9.3">
  <extractioninfo>
    <devicename>Samsung Galaxy S21</devicename>
    <imei>123456789012345</imei>
    <imsi>234150000000000</imsi>
    <iccid>8944110000000000</iccid>
    <manufacturer>Samsung</manufacturer>
    <model>SM-G991B</model>
    <osversion>Android 12</osversion>
    <extractiontype>Full File System</extractiontype>
    <extractiondate>2024-03-15T10:30:00</extractiondate>
    <xryversion>9.3.1</xryversion>
    <casenumber>CASE-2024-001</casenumber>
    <examiner>J. Smith</examiner>
  </extractioninfo>
  <data>
    <item type="Contact" deleted="false" id="1" source="Contacts/Phone">
      <field name="Name">Alice Wonderland</field>
      <field name="FirstName">Alice</field>
      <field name="LastName">Wonderland</field>
      <field name="Phone" phonetype="Mobile">+441234567890</field>
      <field name="Phone" phonetype="Home">+441234000000</field>
      <field name="Email" emailtype="Personal">alice@example.com</field>
      <field name="Organisation">ACME Corp</field>
      <field name="Account">Google</field>
    </item>
    <item type="Contact" deleted="true" id="2" source="Contacts/SIM">
      <field name="Name">Bob Builder</field>
      <field name="Phone" phonetype="Mobile">+447700000001</field>
    </item>
    <item type="Call" deleted="false" id="10" source="Call Log/Phone">
      <field name="Direction">Incoming</field>
      <field name="Number">+441234567890</field>
      <field name="Name">Alice Wonderland</field>
      <field name="Time">2024-03-15T08:00:00</field>
      <field name="Duration">00:02:35</field>
      <field name="CallType">Voice</field>
    </item>
    <item type="SMS" deleted="false" id="20" source="SMS/Phone">
      <field name="Direction">Incoming</field>
      <field name="From">+441234567890</field>
      <field name="Body">Hello, how are you?</field>
      <field name="Time">2024-03-15T09:00:00</field>
      <field name="Read">true</field>
      <field name="ThreadID">5</field>
    </item>
    <item type="SMS" deleted="true" id="21" source="SMS/Phone">
      <field name="Direction">Outgoing</field>
      <field name="To">+441234567890</field>
      <field name="Body">secret message</field>
      <field name="Time">2024-03-14T22:00:00</field>
    </item>
    <item type="Location" deleted="false" id="30" source="GPS">
      <field name="Latitude">51.5074</field>
      <field name="Longitude">-0.1278</field>
      <field name="Altitude">15.3</field>
      <field name="Accuracy">10.0</field>
      <field name="Time">2024-03-15T07:30:00</field>
      <field name="Type">GPS</field>
    </item>
    <item type="Installed Application" deleted="false" id="40" source="Applications">
      <field name="Name">WhatsApp</field>
      <field name="PackageName">com.whatsapp</field>
      <field name="Version">2.24.1.76</field>
      <field name="InstallDate">2023-01-10T12:00:00</field>
      <field name="SystemApp">false</field>
    </item>
    <item type="Wireless Network" deleted="false" id="50" source="WiFi">
      <field name="SSID">HomeNetwork</field>
      <field name="BSSID">AA:BB:CC:DD:EE:FF</field>
      <field name="Security">WPA2-PSK</field>
      <field name="LastConnected">2024-03-15T06:00:00</field>
      <field name="Password">mysecret123</field>
    </item>
  </data>
</xry>
"""


@pytest.fixture
def xry_file(tmp_path):
    """Write minimal XRY XML to a temp file and return its path."""
    p = tmp_path / "test.xry"
    p.write_bytes(MINIMAL_XRY.encode("utf-8"))
    return str(p)


@pytest.fixture
def report(xry_file):
    return XRYReport(xry_file)


# ======================================================================== #
#  Utility tests                                                            #
# ======================================================================== #


class TestUtils:
    def test_parse_datetime_iso(self):
        dt = parse_datetime("2024-03-15T10:30:00")
        assert dt is not None
        assert dt.year == 2024 and dt.month == 3 and dt.day == 15

    def test_parse_datetime_unix(self):
        dt = parse_datetime(1710499800)
        assert dt is not None
        assert dt.year == 2024

    def test_parse_datetime_none(self):
        assert parse_datetime(None) is None
        assert parse_datetime("") is None

    def test_parse_bool(self):
        assert parse_bool("true") is True
        assert parse_bool("yes") is True
        assert parse_bool("false") is False
        assert parse_bool("0") is False
        assert parse_bool(None) is None

    def test_parse_int(self):
        assert parse_int("42") == 42
        assert parse_int("  7  ") == 7
        assert parse_int("abc") is None
        assert parse_int(None) is None

    def test_normalise_phone(self):
        assert normalise_phone("+44 1234 567 890") == "+441234567890"
        assert normalise_phone("(800) 555-1234") == "8005551234"
        assert normalise_phone(None) is None

    def test_parse_direction(self):
        assert parse_direction("Incoming") == "Incoming"
        assert parse_direction("sent") == "Outgoing"
        assert parse_direction("missed") == "Missed"
        assert parse_direction(None) is None

    def test_parse_coordinates(self):
        lat, lon = parse_coordinates("51.5074", "-0.1278")
        assert abs(lat - 51.5074) < 0.0001
        assert abs(lon + 0.1278) < 0.0001

    def test_parse_coordinates_combined(self):
        lat, lon = parse_coordinates("51.5074 -0.1278", None)
        assert abs(lat - 51.5074) < 0.0001


# ======================================================================== #
#  Parser tests                                                             #
# ======================================================================== #


class TestXRYParser:
    def test_load_valid(self, xry_file):
        parser = XRYParser(xry_file).load()
        assert parser.version == "9.3"

    def test_file_not_found(self):
        with pytest.raises(XRYFileNotFoundError):
            XRYParser("/nonexistent/path.xry").load()

    def test_invalid_xml(self, tmp_path):
        bad = tmp_path / "bad.xry"
        bad.write_text("<<not valid xml>>")
        with pytest.raises(XRYParseError):
            XRYParser(str(bad)).load()

    def test_extraction_info(self, xry_file):
        parser = XRYParser(xry_file).load()
        info = parser.extraction_info
        assert info.get("devicename") == "Samsung Galaxy S21"
        assert info.get("imei") == "123456789012345"

    def test_iter_items(self, xry_file):
        parser = XRYParser(xry_file).load()
        items = list(parser.iter_items())
        categories = {cat for cat, _ in items}
        assert "contacts" in categories
        assert "calls" in categories
        assert "messages" in categories

    def test_items_by_category_contacts(self, xry_file):
        parser = XRYParser(xry_file).load()
        grouped = parser.items_by_category()
        assert len(grouped.get("contacts", [])) == 2

    def test_deleted_flag_in_fields(self, xry_file):
        parser = XRYParser(xry_file).load()
        grouped = parser.items_by_category()
        contacts = grouped["contacts"]
        deleted = [c for c in contacts if c["_deleted"]]
        assert len(deleted) == 1


# ======================================================================== #
#  Report / model tests                                                     #
# ======================================================================== #


class TestXRYReport:
    def test_repr(self, report):
        r = repr(report)
        assert "XRYReport" in r

    def test_device_info(self, report):
        d = report.device
        assert d.device_name == "Samsung Galaxy S21"
        assert d.imei == "123456789012345"
        assert d.manufacturer == "Samsung"
        assert d.model == "SM-G991B"
        assert d.examiner == "J. Smith"

    def test_contacts_count(self, report):
        assert len(report.contacts) == 2

    def test_contact_fields(self, report):
        alice = next(c for c in report.contacts if c.name == "Alice Wonderland")
        assert alice.first_name == "Alice"
        assert alice.last_name == "Wonderland"
        assert len(alice.phone_numbers) == 2
        assert alice.primary_phone == "+441234567890"
        assert alice.primary_email == "alice@example.com"
        assert alice.organisation == "ACME Corp"
        assert not alice.deleted

    def test_deleted_contact(self, report):
        bob = next(c for c in report.contacts if "Bob" in (c.name or ""))
        assert bob.deleted

    def test_calls(self, report):
        assert len(report.calls) == 1
        call = report.calls[0]
        assert call.direction == "Incoming"
        assert call.number == "+441234567890"
        assert call.duration == 155  # 2m35s
        assert call.duration_formatted == "00:02:35"

    def test_messages_count(self, report):
        assert len(report.messages) == 2

    def test_message_incoming(self, report):
        msg = next(m for m in report.messages if not m.deleted)
        assert msg.is_incoming
        assert msg.body == "Hello, how are you?"
        assert msg.read is True

    def test_deleted_message(self, report):
        deleted = [m for m in report.messages if m.deleted]
        assert len(deleted) == 1
        assert "secret" in deleted[0].body

    def test_locations(self, report):
        assert len(report.locations) == 1
        loc = report.locations[0]
        assert abs(loc.latitude - 51.5074) < 0.0001
        assert abs(loc.longitude + 0.1278) < 0.0001
        assert loc.coordinates == (loc.latitude, loc.longitude)

    def test_installed_apps(self, report):
        assert len(report.installed_apps) == 1
        app = report.installed_apps[0]
        assert app.name == "WhatsApp"
        assert app.package_name == "com.whatsapp"
        assert not app.is_system_app

    def test_wireless_networks(self, report):
        assert len(report.wireless_networks) == 1
        wifi = report.wireless_networks[0]
        assert wifi.ssid == "HomeNetwork"
        assert wifi.bssid == "AA:BB:CC:DD:EE:FF"
        assert wifi.password == "mysecret123"

    def test_search_messages(self, report):
        results = report.search_messages("hello")
        assert len(results) == 1

    def test_search_messages_case_insensitive(self, report):
        results = report.search_messages("HELLO")
        assert len(results) == 1

    def test_deleted_items_helper(self, report):
        deleted_msgs = report.deleted_items("messages")
        assert all(m.deleted for m in deleted_msgs)

    def test_contacts_by_name(self, report):
        results = report.contacts_by_name("alice")
        assert len(results) == 1

    def test_locations_with_gps(self, report):
        gps_locs = report.locations_with_gps()
        assert len(gps_locs) == 1

    def test_summary(self, report):
        s = report.summary()
        assert s["device"] == "Samsung Galaxy S21"
        assert s["counts"]["contacts"] == 2
        assert s["counts"]["calls"] == 1
        assert s["counts"]["messages"] == 2

    def test_to_json(self, report):
        import json

        data = json.loads(report.to_json())
        assert "contacts" in data
        assert "calls" in data
        assert len(data["contacts"]) == 2

    def test_xry_version(self, report):
        assert report.xry_version == "9.3"

    def test_iter_all_artifacts(self, report):
        all_artifacts = list(report.iter_all_artifacts())
        # Should include contacts, calls, messages, location, app, wifi
        assert len(all_artifacts) >= 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
