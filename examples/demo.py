#!/usr/bin/env python3
"""
examples/demo.py — Demonstrates xrylib usage with a synthetic .xry file.

Run from the repo root:
    python examples/demo.py
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SAMPLE_XRY = """<?xml version="1.0" encoding="UTF-8"?>
<xry version="9.3">
  <extractioninfo>
    <devicename>iPhone 14 Pro</devicename>
    <imei>356938035643809</imei>
    <manufacturer>Apple</manufacturer>
    <model>iPhone15,2</model>
    <osversion>iOS 17.2.1</osversion>
    <extractiontype>Full File System</extractiontype>
    <extractiondate>2024-06-01T09:00:00</extractiondate>
    <casenumber>CASE-2024-042</casenumber>
    <examiner>D. Jones</examiner>
  </extractioninfo>
  <data>
    <item type="Contact" id="1" source="Contacts/Phone">
      <field name="Name">Eve Torres</field>
      <field name="Phone" phonetype="Mobile">+15551234567</field>
      <field name="Email">eve@example.com</field>
      <field name="Organisation">Initech</field>
    </item>
    <item type="Contact" id="2" deleted="true" source="Contacts/SIM">
      <field name="Name">Deleted Person</field>
      <field name="Phone" phonetype="Mobile">+15557654321</field>
    </item>
    <item type="Call" id="10" source="Call Log">
      <field name="Direction">Outgoing</field>
      <field name="Number">+15551234567</field>
      <field name="Name">Eve Torres</field>
      <field name="Time">2024-05-31T14:22:00</field>
      <field name="Duration">00:05:10</field>
      <field name="CallType">Voice</field>
    </item>
    <item type="SMS" id="20" source="Messages">
      <field name="Direction">Incoming</field>
      <field name="From">+15551234567</field>
      <field name="Body">Meet me at the park at 5pm</field>
      <field name="Time">2024-05-31T16:00:00</field>
      <field name="Read">true</field>
    </item>
    <item type="Chat Message" id="30" source="WhatsApp">
      <field name="Application">WhatsApp</field>
      <field name="Direction">Incoming</field>
      <field name="Sender">+15551234567</field>
      <field name="SenderName">Eve Torres</field>
      <field name="Body">Don't forget the docs!</field>
      <field name="Time">2024-05-31T17:30:00</field>
    </item>
    <item type="Location" id="40" source="GPS">
      <field name="Latitude">40.7128</field>
      <field name="Longitude">-74.0060</field>
      <field name="Altitude">10.0</field>
      <field name="Accuracy">5.0</field>
      <field name="Time">2024-05-31T17:00:00</field>
      <field name="Type">GPS</field>
    </item>
    <item type="Browser History" id="50" source="Safari">
      <field name="URL">https://maps.google.com</field>
      <field name="Title">Google Maps</field>
      <field name="Browser">Safari</field>
      <field name="LastVisited">2024-05-31T16:55:00</field>
      <field name="VisitCount">3</field>
    </item>
    <item type="Wireless Network" id="60" source="WiFi">
      <field name="SSID">CafeWiFi_Free</field>
      <field name="BSSID">AA:BB:CC:11:22:33</field>
      <field name="Security">Open</field>
      <field name="LastConnected">2024-05-31T16:30:00</field>
    </item>
    <item type="Installed Application" id="70" source="Applications">
      <field name="Name">Signal</field>
      <field name="PackageName">org.thoughtcrime.securesms</field>
      <field name="Version">6.37.3</field>
      <field name="InstallDate">2023-06-15T08:00:00</field>
    </item>
  </data>
</xry>
"""


def main():
    # Write sample XRY to a temp file
    with tempfile.NamedTemporaryFile(suffix=".xry", mode="wb", delete=False) as f:
        f.write(SAMPLE_XRY.encode("utf-8"))
        path = f.name

    try:
        from xrylib import XRYReport

        print("=" * 60)
        print("  xrylib — Forensic XRY Report Demo")
        print("=" * 60)

        report = XRYReport(path)
        print(f"\n{report}\n")

        # ── Device info ─────────────────────────────────────────────
        print("── DEVICE ─────────────────────────────────────")
        d = report.device
        print(f"  Name        : {d.device_name}")
        print(f"  IMEI        : {d.imei}")
        print(f"  OS          : {d.os_version}")
        print(f"  Extraction  : {d.extraction_type}")
        print(f"  Date        : {d.extraction_date}")
        print(f"  Examiner    : {d.examiner}")
        print(f"  Case #      : {d.case_number}")

        # ── Contacts ────────────────────────────────────────────────
        print("\n── CONTACTS ────────────────────────────────────")
        for c in report.contacts:
            flag = "[DELETED] " if c.deleted else ""
            print(f"  {flag}{c.name} | {c.primary_phone} | {c.primary_email}")

        # ── Calls ───────────────────────────────────────────────────
        print("\n── CALLS ───────────────────────────────────────")
        for call in report.calls:
            print(
                f"  [{call.direction}] {call.number} ({call.name}) "
                f"@ {call.timestamp}  dur={call.duration_formatted}"
            )

        # ── Messages ────────────────────────────────────────────────
        print("\n── SMS MESSAGES ────────────────────────────────")
        for msg in report.messages:
            flag = "[DELETED] " if msg.deleted else ""
            print(f"  {flag}[{msg.direction}] {msg.sender}: {msg.body!r}")

        # ── Chat ────────────────────────────────────────────────────
        print("\n── CHAT MESSAGES ───────────────────────────────")
        for cm in report.chat_messages:
            print(f"  [{cm.application}] {cm.sender_name}: {cm.body!r}")

        # ── Locations ───────────────────────────────────────────────
        print("\n── LOCATIONS ───────────────────────────────────")
        for loc in report.locations_with_gps():
            print(
                f"  ({loc.latitude}, {loc.longitude})  alt={loc.altitude}m  @ {loc.timestamp}"
            )

        # ── Browser ─────────────────────────────────────────────────
        print("\n── BROWSER HISTORY ─────────────────────────────")
        for bh in report.browser_history:
            print(f"  [{bh.browser}] {bh.url}  visits={bh.visit_count}")

        # ── Wi-Fi ───────────────────────────────────────────────────
        print("\n── WIRELESS NETWORKS ───────────────────────────")
        for wn in report.wireless_networks:
            print(f"  {wn.ssid!r} ({wn.bssid}) [{wn.security}]")

        # ── Apps ────────────────────────────────────────────────────
        print("\n── INSTALLED APPS ──────────────────────────────")
        for app in report.installed_apps:
            print(f"  {app.name}  v{app.version}  [{app.package_name}]")

        # ── Summary ─────────────────────────────────────────────────
        print("\n── SUMMARY ─────────────────────────────────────")
        print(report.summary_json())

        # ── Search ──────────────────────────────────────────────────
        print("\n── SEARCH: messages containing 'park' ──────────")
        for m in report.search_messages("park"):
            print(f"  {m.body!r}")

        print("\nDemo complete.")

    finally:
        os.unlink(path)


if __name__ == "__main__":
    main()
