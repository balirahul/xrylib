"""
xrylib.exceptions — Custom exception types for XRY parsing errors.
"""


class XRYError(Exception):
    """Base exception for all xrylib errors."""


class XRYFileNotFoundError(XRYError, FileNotFoundError):
    """Raised when the .xry file does not exist or cannot be opened."""


class XRYParseError(XRYError, ValueError):
    """Raised when the .xry file cannot be parsed (malformed XML, unexpected structure)."""


class XRYUnsupportedVersionError(XRYError):
    """Raised when the XRY file version is not supported by this library."""

    def __init__(self, version: str):
        self.version = version
        super().__init__(f"Unsupported XRY file version: {version!r}")


class XRYExtractionError(XRYError):
    """Raised when a specific artifact type cannot be extracted."""

    def __init__(self, artifact_type: str, reason: str = ""):
        self.artifact_type = artifact_type
        self.reason = reason
        msg = f"Failed to extract artifact type {artifact_type!r}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
