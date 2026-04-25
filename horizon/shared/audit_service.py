"""Journal d'audit immuable (POL-SEC-03)."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from horizon.shared.models import AuditLog

logger = logging.getLogger("horizon.audit")


def log_action(
    db: Session,
    actor_id,
    action,
    target_type: Optional[str] = None,
    target_id=None,
    ip_address: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    try:
        entry = AuditLog(
            id=uuid.uuid4(),
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id if target_id else None,
            ip_address=ip_address,
            log_metadata=metadata or {},
            timestamp=datetime.now(timezone.utc),
        )
        db.add(entry)
    except Exception as e:
        logger.error("Échec écriture audit log : %s", e)
