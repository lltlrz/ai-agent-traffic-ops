import pandas as pd

from traffic_agent.analytics import (
    clean_events,
    compute_funnel,
    failure_reason_breakdown,
)


def test_clean_events_deduplicates_and_normalizes_missing_error_code():
    rows = [
        {"event_id": "e1", "user_id": "u1", "event_name": "exposure", "event_time": "2026-09-01", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "新用户", "error_code": None},
        {"event_id": "e1", "user_id": "u1", "event_name": "exposure", "event_time": "2026-09-01", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "新用户", "error_code": None},
    ]
    cleaned, quality = clean_events(pd.DataFrame(rows))
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["error_code"] == "NO_ERROR"
    assert quality["duplicate_events_removed"] == 1


def test_clean_events_rejects_missing_required_fields():
    try:
        clean_events(pd.DataFrame([{"event_id": "e1"}]))
    except ValueError as exc:
        assert "缺少字段" in str(exc)
        assert "user_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_compute_funnel_uses_unique_users_and_handles_zero_denominator():
    events = pd.DataFrame(
        [
            {"user_id": "u1", "event_name": "exposure"},
            {"user_id": "u1", "event_name": "click"},
            {"user_id": "u1", "event_name": "coupon_claim"},
            {"user_id": "u2", "event_name": "exposure"},
        ]
    )
    funnel = compute_funnel(events)
    assert funnel["exposure_users"] == 2
    assert funnel["ctr"] == 0.5
    assert funnel["click_to_claim_rate"] == 1.0
    empty = compute_funnel(events.iloc[0:0])
    assert empty["ctr"] is None
    assert empty["click_to_claim_rate"] is None


def test_failure_reason_breakdown_only_counts_failed_claims():
    events = pd.DataFrame(
        [
            {"event_name": "coupon_claim_fail", "error_code": "OUT_OF_STOCK", "user_id": "u1"},
            {"event_name": "coupon_claim_fail", "error_code": "OUT_OF_STOCK", "user_id": "u2"},
            {"event_name": "coupon_claim", "error_code": "NO_ERROR", "user_id": "u3"},
        ]
    )
    result = failure_reason_breakdown(events)
    assert result.iloc[0]["error_code"] == "OUT_OF_STOCK"
    assert result.iloc[0]["failed_users"] == 2

