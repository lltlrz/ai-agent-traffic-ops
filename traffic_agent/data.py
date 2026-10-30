from pathlib import Path

import pandas as pd

from .analytics import clean_events


def load_data(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    data_dir = Path(data_dir)
    #读取事件数据和活动数据
    events = pd.read_csv(data_dir / "events.csv")
    campaigns = pd.read_csv(data_dir / "campaigns.csv")
    required_campaigns = {"campaign_id", "campaign_name", "budget", "coupon_stock"}
    missing = required_campaigns - set(campaigns.columns)
    if missing:
        raise ValueError(f"campaigns.csv 缺少字段: {', '.join(sorted(missing))}")
    events, quality = clean_events(events)
    return events, campaigns, quality
