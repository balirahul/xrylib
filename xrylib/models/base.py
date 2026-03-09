"""
xrylib.models.base — Base dataclass for all forensic artifact models.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ForensicArtifact:
    """
    Base class for all forensic artifacts extracted from an XRY file.

    Attributes:
        raw_fields:     Original key-value pairs from the XRY XML node.
        deleted:        True if the artifact was marked as deleted/recovered.
        source:         The internal XRY data source path (e.g. 'Contacts/SIM').
        item_id:        Unique item identifier assigned by XRY.
        timestamp_parsed: When this artifact was parsed by xrylib.
    """

    raw_fields: Dict[str, Any] = field(default_factory=dict, repr=False)
    deleted: bool = False
    source: Optional[str] = None
    item_id: Optional[str] = None
    timestamp_parsed: datetime = field(default_factory=datetime.utcnow, repr=False)

    # ------------------------------------------------------------------ #
    # Serialisation helpers                                                #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain dict representation of this artifact."""
        d = asdict(self)
        # Convert datetime objects to ISO strings for JSON-friendliness
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Return a JSON string representation of this artifact."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    # ------------------------------------------------------------------ #
    # Helper: pull a field from raw_fields with an optional default       #
    # ------------------------------------------------------------------ #

    def get_field(self, name: str, default: Any = None) -> Any:
        """Retrieve a value from the original XRY raw fields dict."""
        return self.raw_fields.get(name, default)

    # ------------------------------------------------------------------ #
    # Dunder helpers                                                       #
    # ------------------------------------------------------------------ #

    def __str__(self) -> str:
        return self.to_json()
