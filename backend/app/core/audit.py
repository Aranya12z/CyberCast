"""
app/core/audit.py — Centralized audit log helper.

Architecture reference: ARCHITECTURE.md §8 (Security & Auditability)
  "Audit log entries: event_id, user, action, timestamp, resource, metadata.
   The architecture must be able to answer: 'Who did what, when, and to which
   intelligence record?'"

All sensitive/state-changing events that must write an audit row (§8):
  - login
  - logout                         (written by auth router)
  - prediction_generated           (written by prediction_orchestration)
  - prediction_viewed
  - alert_generated / alert_acknowledged
  - intelligence_report_created
  - data_modification
  - administrative_action

Usage:
    from app.core.audit import audit_log
    audit_log(db, action="login", user_id=user.user_id, resource=f"user:{user.user_id}",
              metadata={"role": user.role})

The helper is intentionally side-effect-free with respect to commits:
callers are responsible for their own db.commit() so that audit rows
are written atomically with the business operation they record.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def audit_log(
    db: Session,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    resource: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Create and add an AuditLog row to the current database session.

    Does NOT commit — the caller controls the transaction boundary so that
    the audit entry is always written atomically with the surrounding business
    operation (e.g., a prediction persist + audit row in a single commit).

    Args:
        db:        Active SQLAlchemy session.
        action:    One of the canonical event names defined in ARCHITECTURE.md §8:
                     login | logout | prediction_generated | prediction_viewed |
                     alert_generated | alert_acknowledged |
                     intelligence_report_created | data_modification |
                     administrative_action
        user_id:   UUID of the acting user (None for system-initiated events).
        resource:  Free-form resource identifier, e.g. "prediction:<uuid>" or
                   "user:<uuid>" — must answer "to which record?".
        metadata:  Arbitrary JSON-serialisable dict with event-specific details
                   (e.g. IP address, outcome, role, model version, etc.).

    Returns:
        The AuditLog ORM instance (already added to session, not yet committed).
    """
    entry = AuditLog(
        event_id=uuid.uuid4(),
        user_id=user_id,
        action=action,
        timestamp=datetime.now(timezone.utc),
        resource=resource,
        metadata_=metadata or {},
    )
    db.add(entry)
    return entry
