import pandas as pd
import pytest


@pytest.fixture
def sample_bundle():
    events = pd.DataFrame(
        [
            {"event_id": "1", "user_id": "u1", "event_time": "2026-09-01 10:00:00", "event_name": "exposure", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "新用户", "error_code": "NO_ERROR"},
            {"event_id": "2", "user_id": "u1", "event_time": "2026-09-01 10:01:00", "event_name": "click", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "新用户", "error_code": "NO_ERROR"},
            {"event_id": "3", "user_id": "u1", "event_time": "2026-09-01 10:02:00", "event_name": "coupon_claim_fail", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "新用户", "error_code": "OUT_OF_STOCK"},
            {"event_id": "4", "user_id": "u2", "event_time": "2026-09-01 10:00:00", "event_name": "exposure", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "老用户", "error_code": "NO_ERROR"},
            {"event_id": "5", "user_id": "u2", "event_time": "2026-09-01 10:01:00", "event_name": "click", "campaign_id": "c1", "resource_position": "首页Banner", "segment": "老用户", "error_code": "NO_ERROR"},
        ]
    )
    campaigns = pd.DataFrame([{"campaign_id": "c1", "campaign_name": "早高峰券", "budget": 10000, "coupon_stock": 100}])
    return events, campaigns
