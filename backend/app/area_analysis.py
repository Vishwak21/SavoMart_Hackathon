from typing import Any

import httpx

LOCALITIES = {
    "t-nagar": {"name": "T. Nagar", "latitude": 13.0418, "longitude": 80.2341},
    "anna-nagar": {"name": "Anna Nagar", "latitude": 13.0850, "longitude": 80.2101},
    "velachery": {"name": "Velachery", "latitude": 12.9815, "longitude": 80.2180},
    "adyar": {"name": "Adyar", "latitude": 13.0012, "longitude": 80.2565},
    "porur": {"name": "Porur", "latitude": 13.0358, "longitude": 80.1560},
    "tambaram": {"name": "Tambaram", "latitude": 12.9249, "longitude": 80.1000},
    "mylapore": {"name": "Mylapore", "latitude": 13.0368, "longitude": 80.2676},
}

DEMO_SIGNALS = {
    "t-nagar": {"residential_features": 81, "commercial_features": 150, "amenities": 18, "road_segments": 44, "transit_points": 5, "competitors": 14},
    "anna-nagar": {"residential_features": 96, "commercial_features": 127, "amenities": 24, "road_segments": 52, "transit_points": 8, "competitors": 8},
    "velachery": {"residential_features": 74, "commercial_features": 108, "amenities": 16, "road_segments": 39, "transit_points": 4, "competitors": 11},
    "adyar": {"residential_features": 69, "commercial_features": 89, "amenities": 22, "road_segments": 36, "transit_points": 6, "competitors": 7},
    "porur": {"residential_features": 63, "commercial_features": 76, "amenities": 14, "road_segments": 33, "transit_points": 3, "competitors": 6},
    "tambaram": {"residential_features": 85, "commercial_features": 135, "amenities": 20, "road_segments": 46, "transit_points": 7, "competitors": 12},
    "mylapore": {"residential_features": 77, "commercial_features": 118, "amenities": 25, "road_segments": 41, "transit_points": 7, "competitors": 10},
}

RADIUS_M = 1200
WEIGHTS = {
    "residential_potential": 25,
    "commercial_demand": 20,
    "amenities": 15,
    "road_accessibility": 15,
    "transit_accessibility": 10,
    "competition": 10,
    "savomart_proximity": 5,
}


def search_localities(query: str) -> list[dict[str, Any]]:
    normalized_query = query.strip().casefold()
    if len(normalized_query) < 2:
        return []

    return [
        {"id": locality_id, **locality}
        for locality_id, locality in LOCALITIES.items()
        if normalized_query in locality["name"].casefold()
    ]


def _overpass_query(latitude: float, longitude: float) -> str:
    return f"""[out:json][timeout:20];
(
  node(around:{RADIUS_M},{latitude},{longitude})[building~"^(apartments|residential|house|semidetached_house|terrace)$"];
  way(around:{RADIUS_M},{latitude},{longitude})[building~"^(apartments|residential|house|semidetached_house|terrace)$"];
  node(around:{RADIUS_M},{latitude},{longitude})[shop];
  way(around:{RADIUS_M},{latitude},{longitude})[shop];
  node(around:{RADIUS_M},{latitude},{longitude})[amenity~"^(school|hospital|clinic|pharmacy|marketplace|bank|university)$"];
  way(around:{RADIUS_M},{latitude},{longitude})[amenity~"^(school|hospital|clinic|pharmacy|marketplace|bank|university)$"];
  way(around:{RADIUS_M},{latitude},{longitude})[highway~"^(primary|secondary|tertiary|residential|unclassified)$"];
  node(around:{RADIUS_M},{latitude},{longitude})[public_transport];
  node(around:{RADIUS_M},{latitude},{longitude})[railway~"^(station|halt|tram_stop)$"];
);
out center tags;"""


def _count_osm_signals(elements: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "residential_features": 0,
        "commercial_features": 0,
        "amenities": 0,
        "road_segments": 0,
        "transit_points": 0,
        "competitors": 0,
    }
    residential_types = {"apartments", "residential", "house", "semidetached_house", "terrace"}
    amenity_types = {"school", "hospital", "clinic", "pharmacy", "marketplace", "bank", "university"}
    transit_types = {"station", "halt", "tram_stop"}
    competitor_types = {"supermarket", "convenience", "grocery"}

    for element in elements:
        tags = element.get("tags", {})
        if tags.get("building") in residential_types:
            counts["residential_features"] += 1
        if "shop" in tags:
            counts["commercial_features"] += 1
            if tags["shop"] in competitor_types:
                counts["competitors"] += 1
        if tags.get("amenity") in amenity_types:
            counts["amenities"] += 1
        if "highway" in tags:
            counts["road_segments"] += 1
        if "public_transport" in tags or tags.get("railway") in transit_types:
            counts["transit_points"] += 1

    return counts


def fetch_area_signals(locality_id: str) -> tuple[dict[str, int], str]:
    locality = LOCALITIES[locality_id]
    try:
        response = httpx.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": _overpass_query(locality["latitude"], locality["longitude"])},
            timeout=25,
            headers={"User-Agent": "SavoSiteScout/0.1 (Savomart Chennai expansion demo)"},
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
        return _count_osm_signals(elements), "OpenStreetMap / Overpass"
    except (httpx.HTTPError, ValueError, TypeError):
        return DEMO_SIGNALS[locality_id].copy(), "Demo sample data"


def score_area(signals: dict[str, int]) -> tuple[int, dict[str, dict[str, int]]]:
    component_scores = {
        "residential_potential": min(100, round(signals["residential_features"] * 100 / 80)),
        "commercial_demand": min(100, round(signals["commercial_features"] * 100 / 120)),
        "amenities": min(100, round(signals["amenities"] * 100 / 20)),
        "road_accessibility": min(100, round(signals["road_segments"] * 100 / 50)),
        "transit_accessibility": min(100, round(signals["transit_points"] * 100 / 8)),
        "competition": max(0, 100 - signals["competitors"] * 6),
        "savomart_proximity": 50,
    }
    breakdown = {
        key: {"score": value, "weight": WEIGHTS[key]}
        for key, value in component_scores.items()
    }
    total = round(sum(item["score"] * item["weight"] / 100 for item in breakdown.values()))
    return total, breakdown


def build_area_report(locality_id: str) -> dict[str, Any]:
    locality = LOCALITIES[locality_id]
    signals, data_source = fetch_area_signals(locality_id)
    fitness_score, score_breakdown = score_area(signals)
    strongest_signal = max(
        (key for key in score_breakdown if key != "savomart_proximity"),
        key=lambda key: score_breakdown[key]["score"],
    )
    highlights = [f"Strongest signal: {strongest_signal.replace('_', ' ')}"]
    risks = []
    if signals["competitors"] >= 10:
        risks.append("High grocery competition in the selected catchment")
    if signals["transit_points"] <= 2:
        risks.append("Limited mapped public transport points")
    if not risks:
        risks.append("Validate rent and street-level demand during field scouting")

    return {
        **locality,
        "locality_id": locality_id,
        "radius_m": RADIUS_M,
        "fitness_score": fitness_score,
        "metrics": {"counts": signals, "score_breakdown": score_breakdown},
        "highlights": highlights,
        "risks": risks,
        "data_source": data_source,
        "is_demo": data_source == "Demo sample data",
    }