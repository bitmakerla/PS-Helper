import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional


DEFAULT_THRESHOLDS = {
    "HIGH": 0.90,
    "GOOD": 0.75,
    "POSSIBLE": 0.60,
    "LOW": 0.0,
    "review_below": 0.75,
    "ambiguity_margin": 0.10,
    "low_similarity_below": 0.60,
}


def _normalize_key(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[®™©]", "", text)
    text = re.sub(r"[^a-zA-Z0-9\+\&\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def _dedupe_values(values: List[Any]) -> List[str]:
    seen = set()
    output = []
    for value in values or []:
        text = str(value).strip() if value is not None else ""
        key = _normalize_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def _similarity(left: Any, right: Any) -> float:
    left_key = _normalize_key(left)
    right_key = _normalize_key(right)
    if not left_key or not right_key:
        return 0.0
    if left_key == right_key:
        return 1.0
    return SequenceMatcher(None, left_key, right_key).ratio()


def _confidence_label(score: float, thresholds: Dict[str, float]) -> str:
    if score >= thresholds["HIGH"]:
        return "HIGH"
    if score >= thresholds["GOOD"]:
        return "GOOD"
    if score >= thresholds["POSSIBLE"]:
        return "POSSIBLE"
    return "LOW"


def _rank_candidates(extracted_value: Any, allowed_values: List[str], top_k: int) -> List[Dict[str, Any]]:
    ranked = [
        {"value": value, "score": round(_similarity(extracted_value, value), 4)}
        for value in allowed_values
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:max(0, top_k)]


def _label_rank(label: str) -> int:
    ranks = {"LOW": 0, "POSSIBLE": 1, "GOOD": 2, "HIGH": 3}
    return ranks.get(str(label or "").upper(), ranks["GOOD"])


def _coerce_score(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _normalize_extracted_values(
    extracted_value: Any = None,
    extracted_values: Optional[List[Any]] = None,
) -> List[Dict[str, Any]]:
    raw_values = extracted_values if extracted_values is not None else [extracted_value]
    signals = []

    for item in raw_values or []:
        if isinstance(item, dict):
            value = item.get("value")
            weight = item.get("weight", 1.0)
            source = item.get("source")
        else:
            value = item
            weight = 1.0
            source = None

        key = _normalize_key(value)
        if not key:
            continue

        try:
            numeric_weight = float(weight)
        except (TypeError, ValueError):
            numeric_weight = 1.0

        if numeric_weight <= 0:
            continue

        signals.append(
            {
                "value": value,
                "weight": numeric_weight,
                "source": source,
            }
        )

    total_weight = sum(item["weight"] for item in signals)
    if total_weight <= 0:
        return []

    return [
        {
            "value": item["value"],
            "weight": round(item["weight"] / total_weight, 4),
            "source": item["source"],
        }
        for item in signals
    ]


def _weighted_similarity(input_signals: List[Dict[str, Any]], candidate: Any) -> float:
    return sum(
        _similarity(signal["value"], candidate) * float(signal["weight"])
        for signal in input_signals
    )


def _rank_weighted_candidates(
    input_signals: List[Dict[str, Any]],
    allowed_values: List[str],
    top_k: int,
) -> List[Dict[str, Any]]:
    ranked = [
        {"value": value, "score": round(_weighted_similarity(input_signals, value), 4)}
        for value in allowed_values
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:max(0, top_k)]


def normalize_with_confidence(
    extracted_value: Any = None,
    allowed_values: Optional[List[Any]] = None,
    *,
    extracted_values: Optional[List[Any]] = None,
    field_name: Optional[str] = None,
    llm_confidence: Optional[float] = None,
    minimum_label: str = "GOOD",
    thresholds: Optional[Dict[str, float]] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Pick the best normalized value from a controlled list and gate it.

    Pass `extracted_value` for the common case, or `extracted_values` with
    weights/sources when multiple signals should contribute to normalization.
    """
    active_thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    allowed = _dedupe_values(allowed_values or [])
    input_signals = _normalize_extracted_values(extracted_value, extracted_values)
    llm_score = _coerce_score(llm_confidence)
    flags = []

    if not input_signals:
        flags.append("missing_extracted_value")
    if not allowed:
        flags.append("empty_allowed_values")

    candidate_ranking = _rank_weighted_candidates(input_signals, allowed, top_k) if input_signals and allowed else []
    best_candidate = candidate_ranking[0] if candidate_ranking else None
    match_score = float(best_candidate.get("score") or 0.0) if best_candidate else 0.0

    if llm_score is not None and best_candidate:
        confidence_score = (match_score * 0.85) + (llm_score * 0.15)
    else:
        confidence_score = match_score

    confidence_score = round(max(0.0, min(1.0, confidence_score)), 4)
    confidence_label = _confidence_label(confidence_score, active_thresholds)
    minimum_label = str(minimum_label or "GOOD").upper()
    accepted = bool(best_candidate) and _label_rank(confidence_label) >= _label_rank(minimum_label)

    if best_candidate and confidence_score < active_thresholds["low_similarity_below"]:
        flags.append("low_similarity_match")
    if best_candidate and not accepted:
        flags.append("below_minimum_threshold")
    if len(candidate_ranking) >= 2:
        top_score = float(candidate_ranking[0].get("score") or 0.0)
        second_score = float(candidate_ranking[1].get("score") or 0.0)
        if top_score - second_score <= active_thresholds["ambiguity_margin"]:
            flags.append("ambiguous_classification")

    suggested_value = best_candidate.get("value") if best_candidate else None
    normalized_value = suggested_value if accepted else None
    if not best_candidate:
        status = "NO_MATCH"
    elif accepted:
        status = "NORMALIZED"
    else:
        status = "SUGGESTED"

    requires_review = not accepted or confidence_score < active_thresholds["review_below"]
    method = "weighted_fuzzy_match" if len(input_signals) > 1 else "fuzzy_match"
    if best_candidate and len(input_signals) == 1 and _normalize_key(input_signals[0]["value"]) == _normalize_key(suggested_value):
        method = "exact_match"

    return {
        "field_name": field_name,
        "extracted_values": input_signals,
        "normalized_value": normalized_value,
        "suggested_value": suggested_value,
        "accepted": accepted,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "normalization": {
            "status": status,
            "method": method if best_candidate else "no_match",
            "match_score": round(match_score, 4),
            "minimum_label": minimum_label,
        },
        "validation": {
            "is_valid": accepted,
            "flags": sorted(set(flags)),
            "requires_review": requires_review,
        },
        "audit": {
            "allowed_values_count": len(allowed),
            "top_candidates": candidate_ranking,
            "input_signals": input_signals,
            "signals": {
                "match_score": round(match_score, 4),
                "llm_confidence_score": round(llm_score, 4) if llm_score is not None else None,
            },
            "thresholds": active_thresholds,
        },
    }


def score_normalized_value(
    extracted_value: Any,
    normalized_value: Any,
    allowed_values: List[Any],
    *,
    field_name: Optional[str] = None,
    llm_confidence: Optional[float] = None,
    top_candidates: Optional[List[Dict[str, Any]]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Score confidence for an extracted value mapped to a normalized value.

    This measures the observable quality of `extracted_value -> normalized_value`
    against a controlled list. It does not claim ground-truth accuracy.
    """
    active_thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    allowed = _dedupe_values(allowed_values)
    allowed_keys = {_normalize_key(value): value for value in allowed}
    normalized_key = _normalize_key(normalized_value)
    extracted_key = _normalize_key(extracted_value)
    llm_score = _coerce_score(llm_confidence)

    flags = []
    if not extracted_key:
        flags.append("missing_extracted_value")
    if not normalized_key:
        flags.append("missing_normalized_value")

    normalized_in_allowed = bool(normalized_key and normalized_key in allowed_keys)
    if normalized_key and not normalized_in_allowed:
        flags.append("taxonomy_missing_candidate")

    if top_candidates is None:
        candidate_ranking = _rank_candidates(extracted_value, allowed, top_k)
    else:
        candidate_ranking = [
            {
                "value": candidate.get("value"),
                "score": round(_coerce_score(candidate.get("score")) or 0.0, 4),
            }
            for candidate in top_candidates[:max(0, top_k)]
            if isinstance(candidate, dict)
        ]

    text_similarity = _similarity(extracted_value, normalized_value)
    allowed_value_score = 1.0 if normalized_in_allowed else 0.0

    method = "no_match"
    if normalized_in_allowed:
        if extracted_key and extracted_key == normalized_key:
            method = "exact_match"
        elif text_similarity > 0:
            method = "fuzzy_match"
        else:
            method = "catalog_match"

    candidate_rank_score = 0.0
    normalized_candidate_score = None
    for index, candidate in enumerate(candidate_ranking):
        if _normalize_key(candidate.get("value")) == normalized_key:
            normalized_candidate_score = float(candidate.get("score") or 0.0)
            candidate_rank_score = max(0.0, 1.0 - (index * 0.2))
            break

    if normalized_candidate_score is None:
        normalized_candidate_score = text_similarity if normalized_in_allowed else 0.0

    if len(candidate_ranking) >= 2 and normalized_in_allowed:
        top_score = float(candidate_ranking[0].get("score") or 0.0)
        second_score = float(candidate_ranking[1].get("score") or 0.0)
        if top_score - second_score <= active_thresholds["ambiguity_margin"]:
            flags.append("ambiguous_classification")

    if text_similarity < active_thresholds["low_similarity_below"] and normalized_in_allowed:
        flags.append("low_similarity_match")

    signals = {
        "allowed_value_score": allowed_value_score,
        "text_similarity_score": round(text_similarity, 4),
        "candidate_rank_score": round(candidate_rank_score, 4),
        "llm_confidence_score": round(llm_score, 4) if llm_score is not None else None,
    }

    weighted_signals = [
        (allowed_value_score, 0.30),
        (text_similarity, 0.35),
        (candidate_rank_score, 0.20),
    ]
    if llm_score is not None:
        weighted_signals.append((llm_score, 0.15))

    total_weight = sum(weight for _, weight in weighted_signals)
    confidence_score = (
        sum(score * weight for score, weight in weighted_signals) / total_weight
        if total_weight
        else 0.0
    )

    if not normalized_in_allowed or not normalized_key or not extracted_key:
        confidence_score = min(confidence_score, 0.59)

    confidence_score = round(max(0.0, min(1.0, confidence_score)), 4)
    confidence_label = _confidence_label(confidence_score, active_thresholds)
    requires_review = confidence_score < active_thresholds["review_below"] or bool(
        {"taxonomy_missing_candidate", "missing_normalized_value", "missing_extracted_value"} & set(flags)
    )

    status = "NORMALIZED" if normalized_in_allowed else "NO_MATCH"
    is_valid = normalized_in_allowed and bool(extracted_key)

    return {
        "field_name": field_name,
        "extracted_value": extracted_value,
        "normalized_value": normalized_value,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "normalization": {
            "status": status,
            "method": method,
            "match_score": round(normalized_candidate_score, 4),
        },
        "validation": {
            "is_valid": is_valid,
            "flags": sorted(set(flags)),
            "requires_review": requires_review,
        },
        "audit": {
            "allowed_values_count": len(allowed),
            "top_candidates": candidate_ranking,
            "signals": signals,
            "thresholds": active_thresholds,
        },
    }
