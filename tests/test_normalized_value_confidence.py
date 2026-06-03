import json

from ps_helper.confidence import normalize_with_confidence, score_normalized_value


def test_exact_match_returns_high_confidence():
    result = score_normalized_value(
        "Serving Trays",
        "Serving Trays",
        ["Serving Trays", "Plates"],
        field_name="category",
    )

    assert result["field_name"] == "category"
    assert result["confidence_label"] == "HIGH"
    assert result["normalization"]["status"] == "NORMALIZED"
    assert result["normalization"]["method"] == "exact_match"
    assert result["validation"]["requires_review"] is False


def test_fuzzy_match_returns_auditable_score():
    result = score_normalized_value(
        "Kitchen tools",
        "Canvas Tools & Accessories",
        ["Kitchen Cookware Sets", "Canvas Tools & Accessories", "Serving Trays"],
    )

    assert result["normalization"]["status"] == "NORMALIZED"
    assert result["normalization"]["method"] == "fuzzy_match"
    assert result["confidence_score"] < 0.75
    assert "low_similarity_match" in result["validation"]["flags"]
    assert result["audit"]["top_candidates"]


def test_normalized_value_outside_allowed_values_returns_no_match():
    result = score_normalized_value(
        "Christmas Decorations",
        "Holiday Decor",
        ["Serving Trays", "Plates"],
    )

    assert result["normalization"]["status"] == "NO_MATCH"
    assert result["validation"]["is_valid"] is False
    assert "taxonomy_missing_candidate" in result["validation"]["flags"]
    assert result["validation"]["requires_review"] is True


def test_missing_values_are_flagged():
    result = score_normalized_value(None, None, ["Serving Trays"])

    assert "missing_extracted_value" in result["validation"]["flags"]
    assert "missing_normalized_value" in result["validation"]["flags"]
    assert result["normalization"]["status"] == "NO_MATCH"
    assert result["validation"]["requires_review"] is True


def test_llm_confidence_contributes_to_score():
    without_llm = score_normalized_value(
        "Serving tray",
        "Serving Trays",
        ["Serving Trays", "Plates"],
    )
    with_llm = score_normalized_value(
        "Serving tray",
        "Serving Trays",
        ["Serving Trays", "Plates"],
        llm_confidence=1.0,
    )

    assert with_llm["confidence_score"] >= without_llm["confidence_score"]
    assert with_llm["audit"]["signals"]["llm_confidence_score"] == 1.0


def test_ambiguous_candidates_are_flagged():
    result = score_normalized_value(
        "Panel",
        "Wall Panel",
        ["Wall Panel", "Ceiling Panel"],
        top_candidates=[
            {"value": "Wall Panel", "score": 0.82},
            {"value": "Ceiling Panel", "score": 0.78},
        ],
    )

    assert "ambiguous_classification" in result["validation"]["flags"]


def test_output_is_json_serializable():
    result = score_normalized_value("Plates", "Plates", ["Plates"])

    json.dumps(result)


def test_normalize_with_confidence_accepts_exact_match():
    result = normalize_with_confidence(
        extracted_value="Serving Trays",
        allowed_values=["Serving Trays", "Plates"],
        minimum_label="GOOD",
    )

    assert result["accepted"] is True
    assert result["normalized_value"] == "Serving Trays"
    assert result["normalization"]["status"] == "NORMALIZED"
    assert result["normalization"]["method"] == "exact_match"


def test_normalize_with_confidence_rejects_below_minimum_label():
    result = normalize_with_confidence(
        extracted_value="Kitchen tools",
        allowed_values=["Kitchen Cookware Sets", "Canvas Tools & Accessories"],
        minimum_label="GOOD",
    )

    assert result["accepted"] is False
    assert result["normalized_value"] is None
    assert result["suggested_value"] is not None
    assert result["normalization"]["status"] == "SUGGESTED"
    assert "below_minimum_threshold" in result["validation"]["flags"]


def test_normalize_with_confidence_accepts_possible_when_configured():
    result = normalize_with_confidence(
        extracted_value="Kitchen tools",
        allowed_values=["Kitchen Cookware Sets", "Canvas Tools & Accessories"],
        minimum_label="POSSIBLE",
    )

    if result["confidence_label"] == "POSSIBLE":
        assert result["accepted"] is True
        assert result["normalized_value"] == result["suggested_value"]


def test_normalize_with_confidence_uses_weighted_inputs():
    result = normalize_with_confidence(
        extracted_values=[
            {"value": "Plates", "weight": 1, "source": "llm"},
            {"value": "Serving Trays", "weight": 9, "source": "breadcrumb"},
        ],
        allowed_values=["Plates", "Serving Trays"],
        minimum_label="GOOD",
    )

    assert result["normalized_value"] == "Serving Trays"
    assert result["normalization"]["method"] == "weighted_fuzzy_match"
    assert result["audit"]["input_signals"][0]["weight"] == 0.1
    assert result["audit"]["input_signals"][1]["weight"] == 0.9


def test_normalize_with_confidence_flags_empty_inputs():
    result = normalize_with_confidence(extracted_value=None, allowed_values=[])

    assert result["accepted"] is False
    assert result["normalization"]["status"] == "NO_MATCH"
    assert "missing_extracted_value" in result["validation"]["flags"]
    assert "empty_allowed_values" in result["validation"]["flags"]


def test_normalize_with_confidence_flags_ambiguous_candidates():
    result = normalize_with_confidence(
        extracted_value="A Panel",
        allowed_values=["B Panel", "C Panel"],
        minimum_label="LOW",
    )

    assert "ambiguous_classification" in result["validation"]["flags"]
