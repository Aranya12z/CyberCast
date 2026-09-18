"""
app/interfaces/__init__.py — Re-exports abstract and concrete interfaces for ML and GIS modules.
"""
from app.interfaces.model_interface import ModelInterface, MockModelInterface
from app.interfaces.spatial_interface import (
    SpatialInterface,
    SpatialService,
    get_spatial_service,
)

__all__ = [
    "ModelInterface",
    "MockModelInterface",
    "SpatialInterface",
    "SpatialService",
    "get_spatial_service",
]
