"""
xrylib.extractors — Functions that convert raw parser field dicts into typed model objects.

Each extractor function accepts a ``fields`` dict (as produced by XRYParser)
and returns an instance of the corresponding model class.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import (
    BrowserHistory,
    CalendarEvent,
    Call,
    ChatMessage,
    Contact,
    DeviceInfo,
    Email,
    EmailAddress,
    GPSCoordinate,
    InstalledApp,
    Location,
    MediaFile,
    Message,
    MessageAttachment,
    Note,
    PhoneNumber,
    UserAccount,
    WirelessNetwork,
)
from ..utils import (
    normalise_str,
    normalise_phone,
    parse_bool,
    parse_coordinates,
    parse_datetime,
    parse_direction,
    parse_float,
    parse_int,
)

# ------------------------------------------------------------------ #
#  Helper: pull a scalar string from a field entry (str or dict)       #
# ------------------------------------------------------------------ #

def _scalar(entry: Any) -> Optional[str]:
    """Extract a plain string value from a raw field entry."""
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry or None
    if isinstance(entry, dict):
        return normalise_str(entry.get("value") or entry.get("Value"))
    return normalise_str(str(entry))


def _list_entries(entry: Any) -> List[Any]:
    """Ensure a field entry is always a list."""
    if entry is None:
        return []
    if isinstance(entry, list):
        return entry
    return [entry]


# ------------------------------------------------------------------ #
#  Device info                                                         #
# ------------------------------------------------------------------ #

def extract_device_info(info: Dict[str, str]) -> DeviceInfo:
    """Build a DeviceInfo from the extractioninfo / deviceinfo flat dict."""
    return DeviceInfo(
        raw_fields=dict(info),
        device_name=normalise_str(info.get("devicename") or info.get("device_name") or info.get("devicefullname")),
        imei=normalise_str(info.get("imei")),
        imei2=normalise_str(info.get("imei2") or info.get("imei_2")),
        imsi=normalise_str(info.get("imsi")),
        iccid=normalise_str(info.get("iccid")),
        msisdn=normalise_str(info.get("msisdn") or info.get("phonenumber") or info.get("phone_number")),
        serial_number=normalise_str(info.get("serialnumber") or info.get("serial_number") or info.get("serial")),
        android_id=normalise_str(info.get("androidid") or info.get("android_id")),
        os_version=normalise_str(info.get("osversion") or info.get("os_version") or info.get("firmwareversion")),
        os_build=normalise_str(info.get("osbuild") or info.get("os_build") or info.get("build")),
        manufacturer=normalise_str(info.get("manufacturer") or info.get("make")),
        model=normalise_str(info.get("model") or info.get("devicemodel")),
        bluetooth_mac=normalise_str(info.get("bluetoothmac") or info.get("bluetooth_mac") or info.get("bluetooth")),
        wifi_mac=normalise_str(info.get("wifimac") or info.get("wifi_mac") or info.get("wifi")),
        extraction_type=normalise_str(info.get("extractiontype") or info.get("type")),
        extraction_date=parse_datetime(info.get("extractiondate") or info.get("date")),
        xry_version=normalise_str(info.get("xryversion") or info.get("version")),
        case_number=normalise_str(info.get("casenumber") or info.get("case")),
        examiner=normalise_str(info.get("examiner") or info.get("operator")),
    )


# ------------------------------------------------------------------ #
#  Contact                                                             #
# ------------------------------------------------------------------ #

def extract_contact(fields: Dict[str, Any]) -> Contact:
    phone_entries = _list_entries(fields.get("Phone") or fields.get("phone") or fields.get("Number"))
    email_entries = _list_entries(fields.get("Email") or fields.get("email") or fields.get("E-mail"))

    phone_numbers: List[PhoneNumber] = []
    for pe in phone_entries:
        num = normalise_phone(_scalar(pe))
        if num:
            ptype = pe.get("phonetype") or pe.get("type") if isinstance(pe, dict) else None
            phone_numbers.append(PhoneNumber(number=num, number_type=normalise_str(ptype)))

    email_addresses: List[EmailAddress] = []
    for ee in email_entries:
        addr = normalise_str(_scalar(ee))
        if addr:
            etype = ee.get("emailtype") or ee.get("type") if isinstance(ee, dict) else None
            email_addresses.append(EmailAddress(address=addr, address_type=normalise_str(etype)))

    return Contact(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        name=normalise_str(_scalar(fields.get("Name") or fields.get("name") or fields.get("FullName"))),
        first_name=normalise_str(_scalar(fields.get("FirstName") or fields.get("First Name") or fields.get("first_name"))),
        last_name=normalise_str(_scalar(fields.get("LastName") or fields.get("Last Name") or fields.get("last_name"))),
        phone_numbers=phone_numbers,
        email_addresses=email_addresses,
        organisation=normalise_str(_scalar(fields.get("Organisation") or fields.get("Company") or fields.get("organization"))),
        title=normalise_str(_scalar(fields.get("Title") or fields.get("JobTitle"))),
        address=normalise_str(_scalar(fields.get("Address") or fields.get("address"))),
        birthday=parse_datetime(_scalar(fields.get("Birthday") or fields.get("DOB"))),
        notes=normalise_str(_scalar(fields.get("Notes") or fields.get("notes") or fields.get("Note"))),
        account=normalise_str(_scalar(fields.get("Account") or fields.get("account"))),
        contact_id=normalise_str(_scalar(fields.get("ID") or fields.get("ContactID"))),
        last_modified=parse_datetime(
            _scalar(fields.get("LastModified") or fields.get("Modified") or fields.get("last_modified"))
        ),
    )


# ------------------------------------------------------------------ #
#  Call                                                                #
# ------------------------------------------------------------------ #

def extract_call(fields: Dict[str, Any]) -> Call:
    raw_dur = _scalar(fields.get("Duration") or fields.get("duration"))
    if raw_dur:
        # Duration may be "00:02:35" or plain seconds
        if ":" in raw_dur:
            parts = raw_dur.split(":")
            try:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
                duration = h * 3600 + m * 60 + s
            except (ValueError, IndexError):
                duration = parse_int(raw_dur)
        else:
            duration = parse_int(raw_dur)
    else:
        duration = None

    return Call(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        direction=parse_direction(_scalar(fields.get("Direction") or fields.get("direction") or fields.get("Type"))),
        number=normalise_phone(
            _scalar(
                fields.get("Number") or fields.get("number")
                or fields.get("PhoneNumber") or fields.get("Remote Party")
            )
        ),
        name=normalise_str(_scalar(fields.get("Name") or fields.get("name") or fields.get("ContactName"))),
        timestamp=parse_datetime(
            _scalar(
                fields.get("Time") or fields.get("Date")
                or fields.get("Timestamp") or fields.get("timestamp")
            )
        ),
        duration=duration,
        call_type=normalise_str(_scalar(fields.get("CallType") or fields.get("call_type") or fields.get("Media"))),
        sim_slot=parse_int(_scalar(fields.get("SIM") or fields.get("Slot") or fields.get("sim_slot"))),
        network=normalise_str(_scalar(fields.get("Network") or fields.get("Carrier"))),
    )


# ------------------------------------------------------------------ #
#  Message (SMS / MMS)                                                 #
# ------------------------------------------------------------------ #

def _extract_attachments(fields: Dict[str, Any]) -> List[MessageAttachment]:
    raw = _list_entries(fields.get("Attachment") or fields.get("attachment") or fields.get("Media"))
    attachments: List[MessageAttachment] = []
    for entry in raw:
        if isinstance(entry, dict):
            attachments.append(MessageAttachment(
                filename=normalise_str(entry.get("filename") or entry.get("Filename") or entry.get("name")),
                mime_type=normalise_str(entry.get("mimetype") or entry.get("MimeType") or entry.get("type")),
                size_bytes=parse_int(entry.get("size") or entry.get("Size")),
                path=normalise_str(entry.get("path") or entry.get("Path")),
            ))
        else:
            path = normalise_str(str(entry))
            if path:
                attachments.append(MessageAttachment(path=path))
    return attachments


def extract_message(fields: Dict[str, Any]) -> Message:
    item_type = (fields.get("_type") or "").upper()
    message_type = "MMS" if "MMS" in item_type else "SMS"
    attachments = _extract_attachments(fields)

    return Message(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        direction=parse_direction(_scalar(fields.get("Direction") or fields.get("direction") or fields.get("Type"))),
        sender=normalise_phone(
            _scalar(
                fields.get("From") or fields.get("Sender")
                or fields.get("sender") or fields.get("Remote Party")
            )
        ),
        receiver=normalise_str(_scalar(fields.get("To") or fields.get("Recipient") or fields.get("receiver"))),
        body=normalise_str(_scalar(fields.get("Body") or fields.get("body") or fields.get("Text") or fields.get("Content"))),
        timestamp=parse_datetime(_scalar(fields.get("Time") or fields.get("Date") or fields.get("Timestamp"))),
        read=parse_bool(_scalar(fields.get("Read") or fields.get("Status"))),
        message_type=message_type,
        thread_id=normalise_str(_scalar(fields.get("ThreadID") or fields.get("thread_id") or fields.get("Thread"))),
        attachments=attachments,
        sim_slot=parse_int(_scalar(fields.get("SIM") or fields.get("Slot"))),
        service_center=normalise_phone(
            _scalar(fields.get("ServiceCenter") or fields.get("service_center") or fields.get("SMSC"))
        ),
    )


# ------------------------------------------------------------------ #
#  Chat Message                                                         #
# ------------------------------------------------------------------ #

def extract_chat_message(fields: Dict[str, Any]) -> ChatMessage:
    app = normalise_str(_scalar(fields.get("Application") or fields.get("App") or fields.get("_type")))
    attachments = _extract_attachments(fields)

    return ChatMessage(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        application=app,
        direction=parse_direction(_scalar(fields.get("Direction") or fields.get("direction") or fields.get("Type"))),
        sender=normalise_str(_scalar(fields.get("From") or fields.get("Sender") or fields.get("sender"))),
        sender_name=normalise_str(_scalar(fields.get("SenderName") or fields.get("sender_name") or fields.get("Name"))),
        receiver=normalise_str(_scalar(fields.get("To") or fields.get("Recipient") or fields.get("receiver"))),
        body=normalise_str(_scalar(fields.get("Body") or fields.get("body") or fields.get("Text") or fields.get("Content"))),
        timestamp=parse_datetime(_scalar(fields.get("Time") or fields.get("Date") or fields.get("Timestamp"))),
        read=parse_bool(_scalar(fields.get("Read") or fields.get("Status"))),
        thread_id=normalise_str(_scalar(fields.get("ThreadID") or fields.get("Thread") or fields.get("Conversation"))),
        attachments=attachments,
        message_status=normalise_str(_scalar(fields.get("MessageStatus") or fields.get("Status"))),
        reply_to_id=normalise_str(_scalar(fields.get("ReplyToID") or fields.get("reply_to"))),
    )


# ------------------------------------------------------------------ #
#  Email                                                               #
# ------------------------------------------------------------------ #

def extract_email(fields: Dict[str, Any]) -> Email:
    def _parse_addr_list(key: str) -> List[str]:
        raw = _scalar(fields.get(key) or fields.get(key.lower()))
        if not raw:
            return []
        return [a.strip() for a in raw.replace(";", ",").split(",") if a.strip()]

    attachments = _extract_attachments(fields)

    return Email(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        sender=normalise_str(_scalar(fields.get("From") or fields.get("Sender"))),
        recipients_to=_parse_addr_list("To"),
        recipients_cc=_parse_addr_list("CC"),
        recipients_bcc=_parse_addr_list("BCC"),
        subject=normalise_str(_scalar(fields.get("Subject") or fields.get("subject"))),
        body=normalise_str(_scalar(fields.get("Body") or fields.get("body") or fields.get("Content"))),
        timestamp=parse_datetime(_scalar(fields.get("Date") or fields.get("Time") or fields.get("Sent"))),
        folder=normalise_str(_scalar(fields.get("Folder") or fields.get("folder") or fields.get("Mailbox"))),
        read=parse_bool(_scalar(fields.get("Read") or fields.get("Status"))),
        has_attachments=len(attachments) > 0,
        attachments=attachments,
        account=normalise_str(_scalar(fields.get("Account") or fields.get("account"))),
        message_id=normalise_str(_scalar(fields.get("MessageID") or fields.get("message_id"))),
    )


# ------------------------------------------------------------------ #
#  Media File                                                          #
# ------------------------------------------------------------------ #

def extract_media_file(fields: Dict[str, Any]) -> MediaFile:
    lat_raw = _scalar(fields.get("Latitude") or fields.get("GPSLatitude") or fields.get("lat"))
    lon_raw = _scalar(fields.get("Longitude") or fields.get("GPSLongitude") or fields.get("lon"))
    lat, lon = parse_coordinates(lat_raw, lon_raw)
    gps: Optional[GPSCoordinate] = None
    if lat is not None and lon is not None:
        alt = parse_float(_scalar(fields.get("Altitude") or fields.get("GPSAltitude")))
        gps = GPSCoordinate(latitude=lat, longitude=lon, altitude=alt)

    return MediaFile(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        filename=normalise_str(_scalar(fields.get("Filename") or fields.get("Name") or fields.get("FileName"))),
        path=normalise_str(_scalar(fields.get("Path") or fields.get("path") or fields.get("FilePath"))),
        media_type=normalise_str(_scalar(fields.get("MediaType") or fields.get("Type") or fields.get("_type"))),
        mime_type=normalise_str(_scalar(fields.get("MimeType") or fields.get("mime_type") or fields.get("ContentType"))),
        size_bytes=parse_int(_scalar(fields.get("Size") or fields.get("FileSize") or fields.get("size"))),
        created=parse_datetime(_scalar(fields.get("Created") or fields.get("CreatedDate") or fields.get("DateCreated"))),
        modified=parse_datetime(_scalar(fields.get("Modified") or fields.get("ModifiedDate") or fields.get("DateModified"))),
        taken=parse_datetime(
            _scalar(
                fields.get("Taken") or fields.get("DateTaken")
                or fields.get("ExifDate") or fields.get("DateTime")
            )
        ),
        width=parse_int(_scalar(fields.get("Width") or fields.get("width"))),
        height=parse_int(_scalar(fields.get("Height") or fields.get("height"))),
        duration=parse_float(_scalar(fields.get("Duration") or fields.get("duration"))),
        gps=gps,
        camera_make=normalise_str(_scalar(fields.get("CameraMake") or fields.get("Make") or fields.get("ExifMake"))),
        camera_model=normalise_str(_scalar(fields.get("CameraModel") or fields.get("Model") or fields.get("ExifModel"))),
        hash_md5=normalise_str(_scalar(fields.get("MD5") or fields.get("md5") or fields.get("HashMD5"))),
        hash_sha256=normalise_str(_scalar(fields.get("SHA256") or fields.get("sha256") or fields.get("HashSHA256"))),
        is_thumbnail=parse_bool(_scalar(fields.get("IsThumbnail") or fields.get("Thumbnail"))) or False,
    )


# ------------------------------------------------------------------ #
#  Location                                                            #
# ------------------------------------------------------------------ #

def extract_location(fields: Dict[str, Any]) -> Location:
    lat_raw = _scalar(fields.get("Latitude") or fields.get("lat") or fields.get("Lat"))
    lon_raw = _scalar(fields.get("Longitude") or fields.get("lon") or fields.get("Lon") or fields.get("Long"))
    lat, lon = parse_coordinates(lat_raw, lon_raw)

    return Location(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        latitude=lat,
        longitude=lon,
        altitude=parse_float(_scalar(fields.get("Altitude") or fields.get("alt"))),
        accuracy=parse_float(_scalar(fields.get("Accuracy") or fields.get("HorizontalAccuracy"))),
        speed=parse_float(_scalar(fields.get("Speed") or fields.get("speed"))),
        bearing=parse_float(_scalar(fields.get("Bearing") or fields.get("Heading"))),
        timestamp=parse_datetime(_scalar(fields.get("Time") or fields.get("Date") or fields.get("Timestamp"))),
        location_type=normalise_str(_scalar(fields.get("Type") or fields.get("PositionType") or fields.get("_type"))),
        address=normalise_str(_scalar(fields.get("Address") or fields.get("address") or fields.get("Location"))),
        source_app=normalise_str(_scalar(fields.get("Application") or fields.get("App") or fields.get("Source"))),
        provider=normalise_str(_scalar(fields.get("Provider") or fields.get("provider"))),
    )


# ------------------------------------------------------------------ #
#  Browser History                                                     #
# ------------------------------------------------------------------ #

def extract_browser_history(fields: Dict[str, Any]) -> BrowserHistory:
    return BrowserHistory(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        url=normalise_str(_scalar(fields.get("URL") or fields.get("url") or fields.get("Address"))),
        title=normalise_str(_scalar(fields.get("Title") or fields.get("title") or fields.get("Name"))),
        visit_count=parse_int(_scalar(fields.get("VisitCount") or fields.get("visit_count") or fields.get("Visits"))),
        last_visited=parse_datetime(_scalar(fields.get("LastVisited") or fields.get("Date") or fields.get("Time"))),
        first_visited=parse_datetime(_scalar(fields.get("FirstVisited") or fields.get("Created"))),
        browser=normalise_str(_scalar(fields.get("Browser") or fields.get("Application") or fields.get("Source"))),
        entry_type=normalise_str(_scalar(fields.get("EntryType") or fields.get("_type"))) or "History",
        username=normalise_str(_scalar(fields.get("Username") or fields.get("User"))),
        password=normalise_str(_scalar(fields.get("Password") or fields.get("password"))),
    )


# ------------------------------------------------------------------ #
#  Installed App                                                       #
# ------------------------------------------------------------------ #

def extract_installed_app(fields: Dict[str, Any]) -> InstalledApp:
    raw_perms = _scalar(fields.get("Permissions") or fields.get("permissions"))
    permissions = [p.strip() for p in (raw_perms or "").split(";") if p.strip()]

    return InstalledApp(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        name=normalise_str(_scalar(fields.get("Name") or fields.get("AppName") or fields.get("ApplicationName"))),
        package_name=normalise_str(
            _scalar(
                fields.get("PackageName") or fields.get("BundleID")
                or fields.get("package_name") or fields.get("Identifier")
            )
        ),
        version=normalise_str(_scalar(fields.get("Version") or fields.get("VersionName"))),
        version_code=parse_int(_scalar(fields.get("VersionCode") or fields.get("version_code") or fields.get("Build"))),
        install_date=parse_datetime(
            _scalar(fields.get("InstallDate") or fields.get("Installed") or fields.get("install_date"))
        ),
        last_used=parse_datetime(_scalar(fields.get("LastUsed") or fields.get("last_used") or fields.get("LastLaunch"))),
        size_bytes=parse_int(_scalar(fields.get("Size") or fields.get("size"))),
        install_source=normalise_str(_scalar(fields.get("InstallSource") or fields.get("Source") or fields.get("Store"))),
        developer=normalise_str(_scalar(fields.get("Developer") or fields.get("Publisher") or fields.get("Author"))),
        is_system_app=parse_bool(_scalar(fields.get("SystemApp") or fields.get("is_system") or fields.get("System"))) or False,
        permissions=permissions,
    )


# ------------------------------------------------------------------ #
#  Note                                                                #
# ------------------------------------------------------------------ #

def extract_note(fields: Dict[str, Any]) -> Note:
    return Note(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        title=normalise_str(_scalar(fields.get("Title") or fields.get("Subject") or fields.get("title"))),
        body=normalise_str(_scalar(fields.get("Body") or fields.get("Content") or fields.get("Text") or fields.get("body"))),
        created=parse_datetime(_scalar(fields.get("Created") or fields.get("Date") or fields.get("created"))),
        modified=parse_datetime(_scalar(fields.get("Modified") or fields.get("modified") or fields.get("LastModified"))),
        account=normalise_str(_scalar(fields.get("Account") or fields.get("account"))),
        folder=normalise_str(_scalar(fields.get("Folder") or fields.get("Notebook") or fields.get("folder"))),
    )


# ------------------------------------------------------------------ #
#  Calendar Event                                                      #
# ------------------------------------------------------------------ #

def extract_calendar_event(fields: Dict[str, Any]) -> CalendarEvent:
    raw_attendees = _scalar(fields.get("Attendees") or fields.get("Participants"))
    attendees = [a.strip() for a in (raw_attendees or "").split(";") if a.strip()]

    return CalendarEvent(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        title=normalise_str(_scalar(fields.get("Title") or fields.get("Subject") or fields.get("Summary"))),
        description=normalise_str(_scalar(fields.get("Description") or fields.get("Body") or fields.get("Notes"))),
        location=normalise_str(_scalar(fields.get("Location") or fields.get("location"))),
        start=parse_datetime(
            _scalar(
                fields.get("Start") or fields.get("StartDate")
                or fields.get("StartTime") or fields.get("Begin")
            )
        ),
        end=parse_datetime(_scalar(fields.get("End") or fields.get("EndDate") or fields.get("EndTime"))),
        all_day=parse_bool(_scalar(fields.get("AllDay") or fields.get("all_day") or fields.get("IsAllDay"))) or False,
        calendar_name=normalise_str(_scalar(fields.get("Calendar") or fields.get("CalendarName"))),
        organiser=normalise_str(_scalar(fields.get("Organiser") or fields.get("Organizer") or fields.get("Organizer"))),
        attendees=attendees,
        recurrence=normalise_str(_scalar(fields.get("Recurrence") or fields.get("RRULE") or fields.get("RecurrenceRule"))),
        alarm_minutes=parse_int(_scalar(fields.get("Alarm") or fields.get("Reminder") or fields.get("AlarmMinutes"))),
    )


# ------------------------------------------------------------------ #
#  Wireless Network                                                    #
# ------------------------------------------------------------------ #

def extract_wireless_network(fields: Dict[str, Any]) -> WirelessNetwork:
    return WirelessNetwork(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        ssid=normalise_str(
            _scalar(fields.get("SSID") or fields.get("ssid") or fields.get("Name") or fields.get("NetworkName"))
        ),
        bssid=normalise_str(
            _scalar(fields.get("BSSID") or fields.get("bssid") or fields.get("MAC") or fields.get("AccessPoint"))
        ),
        security=normalise_str(_scalar(fields.get("Security") or fields.get("SecurityType") or fields.get("Encryption"))),
        frequency=parse_int(_scalar(fields.get("Frequency") or fields.get("frequency") or fields.get("Channel"))),
        signal_strength=parse_int(_scalar(fields.get("SignalStrength") or fields.get("RSSI") or fields.get("Signal"))),
        last_connected=parse_datetime(_scalar(fields.get("LastConnected") or fields.get("LastSeen") or fields.get("Date"))),
        first_connected=parse_datetime(
            _scalar(fields.get("FirstConnected") or fields.get("FirstSeen") or fields.get("Created"))
        ),
        password=normalise_str(_scalar(fields.get("Password") or fields.get("Passphrase") or fields.get("Key"))),
        ip_address=normalise_str(_scalar(fields.get("IPAddress") or fields.get("IP") or fields.get("ip_address"))),
    )


# ------------------------------------------------------------------ #
#  User Account                                                        #
# ------------------------------------------------------------------ #

def extract_user_account(fields: Dict[str, Any]) -> UserAccount:
    return UserAccount(
        raw_fields=fields,
        deleted=fields.get("_deleted", False),
        source=fields.get("_source"),
        item_id=fields.get("_id"),
        account_type=normalise_str(
            _scalar(
                fields.get("AccountType") or fields.get("Type")
                or fields.get("Service") or fields.get("_type")
            )
        ),
        username=normalise_str(_scalar(fields.get("Username") or fields.get("User") or fields.get("Login"))),
        password=normalise_str(_scalar(fields.get("Password") or fields.get("password"))),
        email=normalise_str(_scalar(fields.get("Email") or fields.get("email") or fields.get("EmailAddress"))),
        added=parse_datetime(_scalar(fields.get("Added") or fields.get("Created") or fields.get("DateAdded"))),
        last_sync=parse_datetime(_scalar(fields.get("LastSync") or fields.get("last_sync") or fields.get("Synced"))),
        server=normalise_str(_scalar(fields.get("Server") or fields.get("Host") or fields.get("URL"))),
    )


# ------------------------------------------------------------------ #
#  Dispatcher                                                          #
# ------------------------------------------------------------------ #

CATEGORY_EXTRACTOR = {
    "contacts": extract_contact,
    "calls": extract_call,
    "messages": extract_message,
    "chat_messages": extract_chat_message,
    "emails": extract_email,
    "media_files": extract_media_file,
    "locations": extract_location,
    "browser_history": extract_browser_history,
    "installed_apps": extract_installed_app,
    "notes": extract_note,
    "calendar_events": extract_calendar_event,
    "wireless_networks": extract_wireless_network,
    "user_accounts": extract_user_account,
}
