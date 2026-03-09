"""
xrylib - Python library for parsing and extracting forensic data from XRY files.

XRY is a mobile forensic tool by MSAB (Micro Systemation AB).
This library provides a structured API to extract and model artifacts from
.xry XML report files similar to how ufedlib-py handles UFED outputs.

Example:
    >>> from xrylib import XRYReport
    >>> report = XRYReport("extraction.xry")
    >>> for msg in report.messages:
    ...     print(msg.sender, msg.body)
"""

__version__ = "1.0.0"
__author__ = "xrylib contributors"
__license__ = "MIT"

from .parser import XRYParser
from .report import XRYReport
from .models import (
    DeviceInfo,
    Contact,
    Call,
    Message,
    Email,
    MediaFile,
    Location,
    BrowserHistory,
    InstalledApp,
    Note,
    CalendarEvent,
    WirelessNetwork,
    UserAccount,
    ChatMessage,
)
from .exceptions import (
    XRYParseError,
    XRYFileNotFoundError,
    XRYUnsupportedVersionError,
    XRYExtractionError,
)

__all__ = [
    "XRYReport",
    "XRYParser",
    "DeviceInfo",
    "Contact",
    "Call",
    "Message",
    "Email",
    "MediaFile",
    "Location",
    "BrowserHistory",
    "InstalledApp",
    "Note",
    "CalendarEvent",
    "WirelessNetwork",
    "UserAccount",
    "ChatMessage",
    "XRYParseError",
    "XRYFileNotFoundError",
    "XRYUnsupportedVersionError",
    "XRYExtractionError",
]
