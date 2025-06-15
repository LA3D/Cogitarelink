"""
Context signal detection for Software 2.0 chain-of-thought scaffolds.

Turn quick ASK/analysis flags into abstract signals that trigger domain expertise.
"""

def detect_entity_signals(type_analysis: dict) -> dict:
    """
    Map quick ASK-based type checks to high-level signals for context enrichment.
    """
    signals = {}
    if type_analysis.get("is_protein"):
        signals["has_sequence"] = "biological_entity_likely"
    if type_analysis.get("is_place"):
        signals["has_coordinates"] = "geographic_entity_likely"
    if type_analysis.get("is_company"):
        signals["has_stock_ticker"] = "business_entity_likely"
    # Always add temporal reasoning trigger
    signals["has_publication_date"] = "temporal_entity_likely"
    return signals

def summarize_property_patterns(type_analysis: dict) -> list[str]:
    """
    Return the list of property-type checks that evaluated to True.
    """
    return [k for k, v in type_analysis.items() if v]