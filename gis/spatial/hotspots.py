"""Hotspot detection and spatial clustering module for CyberCast GIS layer.

Performs spatial clustering of historical cybercrime and cash-out locations
using density-based spatial clustering (DBSCAN) with Haversine distance.
Specified in docs/GIS_SPEC.md.
"""

from typing import Any, Dict, List, Set, Tuple
import math

from gis.spatial.distance import extract_coordinates, haversine_distance


def detect_spatial_hotspots(
    incidents: List[Dict[str, Any]],
    eps_km: float = 1.5,
    min_samples: int = 3,
) -> List[Dict[str, Any]]:
    """Detect crime or cash-out hotspots using density-based spatial clustering (DBSCAN).

    Args:
        incidents: List of spatial incident dicts (crimes, withdrawals).
        eps_km: Neighborhood radius in kilometers (default: 1.5 km).
        min_samples: Minimum number of incident points required to form a dense cluster.

    Returns:
        List of cluster hotspot dicts:
        [
            {
                "cluster_id": int,
                "incident_count": int,
                "centroid": {"lat": float, "lng": float},
                "radius_km": float,
                "bounding_box": {
                    "min_lat": float,
                    "max_lat": float,
                    "min_lng": float,
                    "max_lng": float
                },
                "incidents": list[dict]
            }
        ]
    """
    if not incidents or len(incidents) < min_samples:
        return []

    # Extract and cache coordinates
    valid_points: List[Tuple[int, Tuple[float, float], Dict[str, Any]]] = []
    for idx, inc in enumerate(incidents):
        if not isinstance(inc, dict):
            continue
        try:
            lat, lng = extract_coordinates(inc)
            valid_points.append((idx, (lat, lng), inc))
        except (ValueError, TypeError):
            continue

    n_points = len(valid_points)
    if n_points < min_samples:
        return []

    # Precompute neighbor lists for each point
    neighbors: List[List[int]] = [[] for _ in range(n_points)]
    for i in range(n_points):
        for j in range(i, n_points):
            if i == j:
                neighbors[i].append(j)
            else:
                dist = haversine_distance(valid_points[i][1], valid_points[j][1])
                if dist <= eps_km:
                    neighbors[i].append(j)
                    neighbors[j].append(i)

    # DBSCAN execution
    visited: Set[int] = set()
    clustered: Set[int] = set()
    clusters: List[List[int]] = []

    for i in range(n_points):
        if i in visited:
            continue
        visited.add(i)

        current_neighbors = list(neighbors[i])
        if len(current_neighbors) < min_samples:
            # Noise point (can still be added to cluster later as border point)
            continue

        # New cluster
        current_cluster: List[int] = [i]
        clustered.add(i)

        neighbor_queue = [n for n in current_neighbors if n != i]
        queue_idx = 0
        while queue_idx < len(neighbor_queue):
            point_idx = neighbor_queue[queue_idx]
            queue_idx += 1

            if point_idx not in visited:
                visited.add(point_idx)
                sub_neighbors = neighbors[point_idx]
                if len(sub_neighbors) >= min_samples:
                    # Core point: expand cluster
                    for sn in sub_neighbors:
                        if sn not in neighbor_queue and sn != i:
                            neighbor_queue.append(sn)

            if point_idx not in clustered:
                clustered.add(point_idx)
                current_cluster.append(point_idx)

        clusters.append(current_cluster)

    # Format hotspot summary results
    hotspots: List[Dict[str, Any]] = []
    for cluster_id, point_indices in enumerate(clusters, start=1):
        cluster_points = [valid_points[idx] for idx in point_indices]
        lats = [p[1][0] for p in cluster_points]
        lngs = [p[1][1] for p in cluster_points]

        centroid_lat = round(sum(lats) / len(lats), 6)
        centroid_lng = round(sum(lngs) / len(lngs), 6)
        centroid = {"lat": centroid_lat, "lng": centroid_lng}

        # Calculate cluster radius (max distance from centroid)
        max_r_km = 0.0
        for p in cluster_points:
            dist = haversine_distance(centroid, p[1])
            if dist > max_r_km:
                max_r_km = dist

        hotspots.append(
            {
                "cluster_id": cluster_id,
                "incident_count": len(cluster_points),
                "centroid": centroid,
                "radius_km": round(max_r_km, 4),
                "bounding_box": {
                    "min_lat": min(lats),
                    "max_lat": max(lats),
                    "min_lng": min(lngs),
                    "max_lng": max(lngs),
                },
                "incidents": [p[2] for p in cluster_points],
            }
        )

    # Sort hotspots by incident count (densest first)
    hotspots.sort(key=lambda h: h["incident_count"], reverse=True)
    return hotspots
