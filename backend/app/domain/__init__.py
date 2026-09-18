"""
app/domain/__init__.py — Re-exports domain orchestration, management, and intelligence functions.
"""
from app.domain.complaint_processing import (
    create_complaint,
    get_complaint,
    list_complaints,
)
from app.domain.atm_management import (
    get_atm,
    get_atms_geojson,
    list_atms,
)
from app.domain.transaction_management import list_transactions
from app.domain.prediction_orchestration import (
    get_latest_prediction_for_crime,
    run_prediction_pipeline,
)
from app.domain.alert_generation import (
    acknowledge_alert,
    evaluate_and_generate_alerts,
    list_alerts,
)
from app.domain.intelligence_generation import generate_intelligence_report
from app.domain.dashboard_summary import get_dashboard_summary

__all__ = [
    "create_complaint",
    "get_complaint",
    "list_complaints",
    "get_atm",
    "get_atms_geojson",
    "list_atms",
    "list_transactions",
    "run_prediction_pipeline",
    "get_latest_prediction_for_crime",
    "evaluate_and_generate_alerts",
    "list_alerts",
    "acknowledge_alert",
    "generate_intelligence_report",
    "get_dashboard_summary",
]
