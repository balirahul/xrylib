"""
xrylib.models — Forensic artifact dataclasses for XRY extractions.

Each class corresponds to a well-known mobile forensic artifact category
mirroring the taxonomy used by MSAB XRY and similar tools (Cellebrite UFED, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import ForensicArtifact


# ======================================================================== #
#  Device / Extraction metadata                                             #
# ======================================================================== #

@dataclass
class DeviceInfo(ForensicArtifact):
    """
    High-level metadata about the device and the XRY extraction session.

    Attributes:
        device_name:        Manufacturer + model string (e.g. 'Samsung Galaxy S21').
        imei:               Primary IMEI.
        imei2:              Secondary IMEI (dual-SIM devices).
        imsi:               International Mobile Subscriber Identity.
        iccid:              SIM card serial number.
        msisdn:             Mobile phone number stored on SIM.
        serial_number:      Device serial / ESN.
        android_id:         Android ID (64-bit hex).
        os_version:         Operating system version string.
        os_build:           OS build fingerprint.
        manufacturer:       Hardware manufacturer.
        model:              Model number / code.
        bluetooth_mac:      Bluetooth hardware address.
        wifi_mac:           Wi-Fi hardware address.
        extraction_type:    Logical / File System / Physical / Full File System.
        extraction_date:    UTC timestamp of the extraction.
        xry_version:        XRY software version used.
        case_number:        Investigator-assigned case reference.
        examiner:           Name of the forensic examiner.
    """

    device_name: Optional[str] = None
    imei: Optional[str] = None
    imei2: Optional[str] = None
    imsi: Optional[str] = None
    iccid: Optional[str] = None
    msisdn: Optional[str] = None
    serial_number: Optional[str] = None
    android_id: Optional[str] = None
    os_version: Optional[str] = None
    os_build: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    bluetooth_mac: Optional[str] = None
    wifi_mac: Optional[str] = None
    extraction_type: Optional[str] = None
    extraction_date: Optional[datetime] = None
    xry_version: Optional[str] = None
    case_number: Optional[str] = None
    examiner: Optional[str] = None


# ======================================================================== #
#  Contacts                                                                 #
# ======================================================================== #

@dataclass
class PhoneNumber:
    """A single phone number entry within a contact."""
    number: str
    number_type: Optional[str] = None   # Mobile, Home, Work, Other …


@dataclass
class EmailAddress:
    """A single e-mail address entry within a contact."""
    address: str
    address_type: Optional[str] = None  # Personal, Work …


@dataclass
class Contact(ForensicArtifact):
    """
    An address-book entry extracted from the device or SIM.

    Attributes:
        name:           Full display name.
        first_name:     Given name.
        last_name:      Surname / family name.
        phone_numbers:  List of phone numbers associated with this contact.
        email_addresses: List of e-mail addresses.
        organisation:   Employer / organisation.
        title:          Job title.
        address:        Postal address string.
        birthday:       Date of birth.
        notes:          Free-text notes attached to the contact.
        photo_path:     Path to an embedded contact photo (within the extraction).
        account:        Account the contact belongs to (e.g. 'Google', 'SIM').
        contact_id:     Internal contact identifier on the device.
        last_modified:  Last modified timestamp.
    """

    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_numbers: List[PhoneNumber] = field(default_factory=list)
    email_addresses: List[EmailAddress] = field(default_factory=list)
    organisation: Optional[str] = None
    title: Optional[str] = None
    address: Optional[str] = None
    birthday: Optional[datetime] = None
    notes: Optional[str] = None
    photo_path: Optional[str] = None
    account: Optional[str] = None
    contact_id: Optional[str] = None
    last_modified: Optional[datetime] = None

    @property
    def primary_phone(self) -> Optional[str]:
        """Convenience accessor for the first phone number."""
        return self.phone_numbers[0].number if self.phone_numbers else None

    @property
    def primary_email(self) -> Optional[str]:
        """Convenience accessor for the first e-mail address."""
        return self.email_addresses[0].address if self.email_addresses else None


# ======================================================================== #
#  Call Logs                                                                #
# ======================================================================== #

@dataclass
class Call(ForensicArtifact):
    """
    A single call log record.

    Attributes:
        direction:      'Incoming' | 'Outgoing' | 'Missed' | 'Rejected' | 'Unknown'.
        number:         Remote party's phone number.
        name:           Remote party's name (if resolved from contacts).
        timestamp:      Date/time the call occurred (UTC).
        duration:       Call duration in seconds.
        call_type:      'Voice' | 'Video' | 'VoIP' | 'Unknown'.
        sim_slot:       SIM slot used (0 or 1, for dual-SIM devices).
        network:        Mobile network / carrier at time of call.
    """

    direction: Optional[str] = None
    number: Optional[str] = None
    name: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration: Optional[int] = None          # seconds
    call_type: Optional[str] = None
    sim_slot: Optional[int] = None
    network: Optional[str] = None

    @property
    def duration_formatted(self) -> Optional[str]:
        """Return duration as HH:MM:SS string."""
        if self.duration is None:
            return None
        h, remainder = divmod(self.duration, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"


# ======================================================================== #
#  SMS / MMS Messages                                                       #
# ======================================================================== #

@dataclass
class MessageAttachment:
    """An attachment within an MMS or chat message."""
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    path: Optional[str] = None          # extraction-internal path


@dataclass
class Message(ForensicArtifact):
    """
    An SMS or MMS message record.

    Attributes:
        direction:      'Incoming' | 'Outgoing' | 'Unknown'.
        sender:         Sender phone number / address.
        receiver:       Recipient phone number(s), comma-separated for MMS group.
        body:           Plain-text message body.
        timestamp:      UTC date/time the message was sent or received.
        read:           True if the message was read.
        message_type:   'SMS' | 'MMS'.
        thread_id:      Conversation thread identifier.
        attachments:    List of MMS attachments.
        sim_slot:       SIM slot (0/1).
        service_center: SMS service centre number.
    """

    direction: Optional[str] = None
    sender: Optional[str] = None
    receiver: Optional[str] = None
    body: Optional[str] = None
    timestamp: Optional[datetime] = None
    read: Optional[bool] = None
    message_type: str = "SMS"
    thread_id: Optional[str] = None
    attachments: List[MessageAttachment] = field(default_factory=list)
    sim_slot: Optional[int] = None
    service_center: Optional[str] = None

    @property
    def is_incoming(self) -> bool:
        return (self.direction or "").lower() == "incoming"

    @property
    def has_attachments(self) -> bool:
        return len(self.attachments) > 0


# ======================================================================== #
#  Email                                                                    #
# ======================================================================== #

@dataclass
class Email(ForensicArtifact):
    """
    An e-mail message extracted from a mail client database.

    Attributes:
        sender:         Sender address.
        recipients_to:  List of To: addresses.
        recipients_cc:  List of Cc: addresses.
        recipients_bcc: List of Bcc: addresses.
        subject:        Message subject.
        body:           Plain-text or HTML body.
        timestamp:      UTC date/time the message was sent/received.
        folder:         Mailbox folder (Inbox, Sent, Drafts …).
        read:           True if message was read.
        has_attachments: True if attachments exist.
        attachments:    Attachment details.
        account:        Mail account (e-mail address of the device owner).
        message_id:     RFC 2822 Message-ID header.
    """

    sender: Optional[str] = None
    recipients_to: List[str] = field(default_factory=list)
    recipients_cc: List[str] = field(default_factory=list)
    recipients_bcc: List[str] = field(default_factory=list)
    subject: Optional[str] = None
    body: Optional[str] = None
    timestamp: Optional[datetime] = None
    folder: Optional[str] = None
    read: Optional[bool] = None
    has_attachments: bool = False
    attachments: List[MessageAttachment] = field(default_factory=list)
    account: Optional[str] = None
    message_id: Optional[str] = None


# ======================================================================== #
#  Chat / Instant Messages                                                  #
# ======================================================================== #

@dataclass
class ChatMessage(ForensicArtifact):
    """
    A message from a third-party chat application (WhatsApp, Telegram, etc.).

    Attributes:
        application:    App name (e.g. 'WhatsApp', 'Telegram', 'Signal').
        direction:      'Incoming' | 'Outgoing' | 'Unknown'.
        sender:         Sender identifier (phone number, username, etc.).
        sender_name:    Display name of the sender.
        receiver:       Recipient identifier.
        body:           Message text.
        timestamp:      UTC send/receive time.
        read:           True if message was read.
        thread_id:      Chat / conversation identifier.
        attachments:    Attached media.
        message_status: 'Sent' | 'Delivered' | 'Read' | 'Failed'.
        reply_to_id:    ID of the message being replied to.
    """

    application: Optional[str] = None
    direction: Optional[str] = None
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    receiver: Optional[str] = None
    body: Optional[str] = None
    timestamp: Optional[datetime] = None
    read: Optional[bool] = None
    thread_id: Optional[str] = None
    attachments: List[MessageAttachment] = field(default_factory=list)
    message_status: Optional[str] = None
    reply_to_id: Optional[str] = None


# ======================================================================== #
#  Media Files                                                              #
# ======================================================================== #

@dataclass
class GPSCoordinate:
    """Embedded GPS coordinate within a media file."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None


@dataclass
class MediaFile(ForensicArtifact):
    """
    An image, video, or audio file from the device storage.

    Attributes:
        filename:       File name.
        path:           Full path within the device file system.
        media_type:     'Image' | 'Video' | 'Audio' | 'Unknown'.
        mime_type:      MIME type string (e.g. 'image/jpeg').
        size_bytes:     File size in bytes.
        created:        File creation timestamp (UTC).
        modified:       File modification timestamp (UTC).
        taken:          EXIF DateTimeOriginal (UTC).
        width:          Image/video width in pixels.
        height:         Image/video height in pixels.
        duration:       Audio/video duration in seconds.
        gps:            Embedded GPS coordinates (from EXIF).
        camera_make:    EXIF camera manufacturer.
        camera_model:   EXIF camera model.
        hash_md5:       MD5 hash of the file content.
        hash_sha256:    SHA-256 hash of the file content.
        is_thumbnail:   True if this is a cached thumbnail.
    """

    filename: Optional[str] = None
    path: Optional[str] = None
    media_type: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    taken: Optional[datetime] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    gps: Optional[GPSCoordinate] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    hash_md5: Optional[str] = None
    hash_sha256: Optional[str] = None
    is_thumbnail: bool = False

    @property
    def size_kb(self) -> Optional[float]:
        return round(self.size_bytes / 1024, 2) if self.size_bytes else None


# ======================================================================== #
#  Location / GPS                                                           #
# ======================================================================== #

@dataclass
class Location(ForensicArtifact):
    """
    A GPS location record (route log, cell tower, Wi-Fi positioning, etc.).

    Attributes:
        latitude:       Decimal degrees (WGS-84).
        longitude:      Decimal degrees (WGS-84).
        altitude:       Altitude in metres above sea level.
        accuracy:       Horizontal accuracy in metres.
        speed:          Speed in km/h.
        bearing:        Bearing / heading in degrees.
        timestamp:      UTC time of the location fix.
        location_type:  'GPS' | 'Cell' | 'WiFi' | 'Network' | 'Unknown'.
        address:        Reverse-geocoded address string.
        source_app:     Application that recorded the location.
        provider:       GPS provider string.
    """

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    bearing: Optional[float] = None
    timestamp: Optional[datetime] = None
    location_type: Optional[str] = None
    address: Optional[str] = None
    source_app: Optional[str] = None
    provider: Optional[str] = None

    @property
    def coordinates(self) -> Optional[tuple]:
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None


# ======================================================================== #
#  Browser History                                                          #
# ======================================================================== #

@dataclass
class BrowserHistory(ForensicArtifact):
    """
    A web browser history entry or bookmark.

    Attributes:
        url:            Full URL.
        title:          Page title.
        visit_count:    Number of times the URL was visited.
        last_visited:   UTC timestamp of the most recent visit.
        first_visited:  UTC timestamp of the first visit.
        browser:        Browser name (Chrome, Firefox, Safari …).
        entry_type:     'History' | 'Bookmark' | 'Download' | 'Cookie' | 'FormData'.
        username:       Auto-fill username (for FormData entries).
        password:       Auto-fill password (for FormData entries, handle carefully!).
    """

    url: Optional[str] = None
    title: Optional[str] = None
    visit_count: Optional[int] = None
    last_visited: Optional[datetime] = None
    first_visited: Optional[datetime] = None
    browser: Optional[str] = None
    entry_type: str = "History"
    username: Optional[str] = None
    password: Optional[str] = None


# ======================================================================== #
#  Installed Applications                                                   #
# ======================================================================== #

@dataclass
class InstalledApp(ForensicArtifact):
    """
    A record for an application installed on the device.

    Attributes:
        name:           Human-readable application name.
        package_name:   Fully-qualified package name (Android) or bundle ID (iOS).
        version:        Version string.
        version_code:   Integer version code (Android).
        install_date:   UTC install timestamp.
        last_used:      UTC last-used timestamp.
        size_bytes:     Application size in bytes.
        install_source: Store or source (Google Play, APK sideload …).
        developer:      Developer / publisher name.
        is_system_app:  True if the app is a system/built-in app.
        permissions:    List of granted permissions.
    """

    name: Optional[str] = None
    package_name: Optional[str] = None
    version: Optional[str] = None
    version_code: Optional[int] = None
    install_date: Optional[datetime] = None
    last_used: Optional[datetime] = None
    size_bytes: Optional[int] = None
    install_source: Optional[str] = None
    developer: Optional[str] = None
    is_system_app: bool = False
    permissions: List[str] = field(default_factory=list)


# ======================================================================== #
#  Notes                                                                    #
# ======================================================================== #

@dataclass
class Note(ForensicArtifact):
    """
    A note or memo from the device.

    Attributes:
        title:      Note title.
        body:       Note content.
        created:    UTC creation timestamp.
        modified:   UTC last-modified timestamp.
        account:    Account the note belongs to.
        folder:     Note folder / notebook.
    """

    title: Optional[str] = None
    body: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    account: Optional[str] = None
    folder: Optional[str] = None


# ======================================================================== #
#  Calendar Events                                                          #
# ======================================================================== #

@dataclass
class CalendarEvent(ForensicArtifact):
    """
    A calendar / agenda event.

    Attributes:
        title:          Event title / subject.
        description:    Event description or notes.
        location:       Physical location string.
        start:          Event start (UTC).
        end:            Event end (UTC).
        all_day:        True if this is an all-day event.
        calendar_name:  Calendar the event belongs to.
        organiser:      Organiser's name or address.
        attendees:      List of attendee names/addresses.
        recurrence:     Recurrence rule string (RFC 5545 RRULE).
        alarm_minutes:  Minutes before start when an alarm fires.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    all_day: bool = False
    calendar_name: Optional[str] = None
    organiser: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    recurrence: Optional[str] = None
    alarm_minutes: Optional[int] = None

    @property
    def duration_hours(self) -> Optional[float]:
        if self.start and self.end:
            return round((self.end - self.start).total_seconds() / 3600, 2)
        return None


# ======================================================================== #
#  Wireless Networks                                                        #
# ======================================================================== #

@dataclass
class WirelessNetwork(ForensicArtifact):
    """
    A Wi-Fi network the device has connected to or detected.

    Attributes:
        ssid:           Network name.
        bssid:          Access point MAC address.
        security:       Security type (WPA2-PSK, WEP, Open …).
        frequency:      Radio frequency in MHz (2412 = 2.4 GHz channel 1).
        signal_strength: RSSI in dBm.
        last_connected: UTC timestamp of last connection.
        first_connected: UTC timestamp of first connection.
        password:       Stored passphrase (if available).
        ip_address:     IP address assigned during last session.
    """

    ssid: Optional[str] = None
    bssid: Optional[str] = None
    security: Optional[str] = None
    frequency: Optional[int] = None
    signal_strength: Optional[int] = None
    last_connected: Optional[datetime] = None
    first_connected: Optional[datetime] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None


# ======================================================================== #
#  User Accounts                                                            #
# ======================================================================== #

@dataclass
class UserAccount(ForensicArtifact):
    """
    An online account or credential stored on the device.

    Attributes:
        account_type:   Service type (Google, Facebook, Twitter …).
        username:       Username / e-mail for the account.
        password:       Stored plaintext or hash (treat with care).
        email:          Associated e-mail address.
        added:          UTC timestamp when the account was added to the device.
        last_sync:      UTC timestamp of last sync.
        server:         Associated server / endpoint URL.
    """

    account_type: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    added: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    server: Optional[str] = None
