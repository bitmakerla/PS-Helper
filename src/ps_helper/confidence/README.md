# Confidence Helpers

Helpers for AI-assisted normalization workflows where an extracted value needs
to be compared with a controlled list of allowed values.

This package does not prove ground-truth accuracy. It estimates normalization
confidence from observable signals such as text similarity, candidate ranking,
allowed-value membership, and optional LLM confidence.

## Available Helpers

Use `normalize_with_confidence` when you do not have a normalized value yet.
It chooses the best allowed value and only accepts it when it reaches your
configured strictness level.

Use `score_normalized_value` when another system already selected a normalized
value and you only want to audit that mapping.

```python
from ps_helper.confidence import normalize_with_confidence, score_normalized_value
```

## Mode 1: Normalize With Confidence

Use this mode for this workflow:

```text
LLM extracted value + allowed values -> normalized value or suggestion
```

### Single Input

```python
audit = normalize_with_confidence(
    extracted_value="Kitchen tools",
    allowed_values=[
        "Kitchen Cookware Sets",
        "Canvas Tools & Accessories",
        "Serving Trays",
    ],
    field_name="category",
    minimum_label="GOOD",
)

category_normalized = audit["normalized_value"]
```

If the best candidate reaches `minimum_label`, `normalized_value` is populated.
If it does not, `normalized_value` is `None` and `suggested_value` contains the
best candidate for review.

### Multiple Weighted Inputs

Use `extracted_values` when you have multiple signals for the same field.

```python
audit = normalize_with_confidence(
    extracted_values=[
        {"value": "Kitchen tools", "weight": 0.7, "source": "llm"},
        {"value": "Kitchen accessories", "weight": 0.2, "source": "breadcrumb"},
        {"value": "Citrus squeezer", "weight": 0.1, "source": "title"},
    ],
    allowed_values=categories,
    field_name="category",
    minimum_label="GOOD",
)
```

Weights are normalized internally. For example, weights `7`, `2`, and `1` become
`0.7`, `0.2`, and `0.1`.

Candidate score formula:

```text
candidate_score =
  similarity(input_1, candidate) * weight_1
+ similarity(input_2, candidate) * weight_2
+ similarity(input_3, candidate) * weight_3
```

The highest-scoring candidate becomes `suggested_value`.

### Normalize Output Shape

```json
{
  "field_name": "category",
  "extracted_values": [
    {"value": "Kitchen tools", "weight": 1.0, "source": null}
  ],
  "normalized_value": null,
  "suggested_value": "Canvas Tools & Accessories",
  "accepted": false,
  "confidence_score": 0.64,
  "confidence_label": "POSSIBLE",
  "normalization": {
    "status": "SUGGESTED",
    "method": "fuzzy_match",
    "match_score": 0.64,
    "minimum_label": "GOOD"
  },
  "validation": {
    "is_valid": false,
    "flags": ["below_minimum_threshold"],
    "requires_review": true
  },
  "audit": {
    "allowed_values_count": 120,
    "top_candidates": [
      {"value": "Canvas Tools & Accessories", "score": 0.64}
    ],
    "input_signals": [],
    "signals": {
      "match_score": 0.64,
      "llm_confidence_score": null
    },
    "thresholds": {}
  }
}
```

### Normalize Statuses

- `NORMALIZED`: best candidate passed `minimum_label` and was accepted.
- `SUGGESTED`: best candidate exists, but did not pass `minimum_label`.
- `NO_MATCH`: no usable input or no allowed values were provided.

## Mode 2: Score Existing Normalized Value

Use this mode for this workflow:

```text
LLM extracted value + existing normalized value + allowed values -> audit score
```

```python
audit = score_normalized_value(
    extracted_value="Kitchen tools",
    normalized_value="Canvas Tools & Accessories",
    allowed_values=[
        "Kitchen Cookware Sets",
        "Canvas Tools & Accessories",
        "Serving Trays",
    ],
    field_name="category",
    llm_confidence=0.82,
)
```

This mode does not choose a normalized value. It evaluates the mapping that was
already chosen by another system.

### Score Formula

When `llm_confidence` is provided:

```text
confidence_score =
  allowed_value_score * 0.30
+ text_similarity_score * 0.35
+ candidate_rank_score * 0.20
+ llm_confidence_score * 0.15
```

When `llm_confidence` is not provided, the available weights are normalized by
their total weight so the missing LLM score does not automatically penalize the
result.

### Score Signals

- `allowed_value_score`: `1.0` when `normalized_value` exists in `allowed_values`, otherwise `0.0`.
- `text_similarity_score`: textual similarity between `extracted_value` and `normalized_value`.
- `candidate_rank_score`: rank quality of `normalized_value` among candidate matches.
- `llm_confidence_score`: optional confidence reported by the LLM, clamped to `0.0..1.0`.

## Thresholds

Default thresholds:

```python
{
    "HIGH": 0.90,
    "GOOD": 0.75,
    "POSSIBLE": 0.60,
    "LOW": 0.0,
    "review_below": 0.75,
    "ambiguity_margin": 0.10,
    "low_similarity_below": 0.60,
}
```

You can override them per call:

```python
audit = normalize_with_confidence(
    extracted_value="Kitchen tools",
    allowed_values=categories,
    minimum_label="POSSIBLE",
    thresholds={"GOOD": 0.80, "review_below": 0.70},
)
```

## Validation Flags

- `missing_extracted_value`: no usable extracted input was provided.
- `missing_normalized_value`: `score_normalized_value` received no normalized value.
- `empty_allowed_values`: `normalize_with_confidence` received no allowed values.
- `taxonomy_missing_candidate`: normalized value is not in `allowed_values`.
- `low_similarity_match`: match score is below `low_similarity_below`.
- `ambiguous_classification`: top candidates are too close based on `ambiguity_margin`.
- `below_minimum_threshold`: candidate did not reach the requested `minimum_label`.

## Recommended Usage In Spiders

```python
audit = normalize_with_confidence(
    extracted_values=[
        {"value": item.get("category_name"), "weight": 0.7, "source": "llm"},
        {"value": item.get("breadcrumb_category"), "weight": 0.2, "source": "breadcrumb"},
        {"value": item.get("title"), "weight": 0.1, "source": "title"},
    ],
    allowed_values=self.allowed_categories,
    field_name="category",
    minimum_label="GOOD",
)

item["category_normalized"] = audit["normalized_value"]
item["category_confidence_audit"] = audit
```
