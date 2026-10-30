from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

#定义漏斗事件和必需的事件列
FUNNEL_EVENTS = ("exposure", "click", "coupon_claim")
REQUIRED_EVENT_COLUMNS = {
    "event_id", "user_id", "event_time", "event_name", "campaign_id",
    "resource_position", "segment", "error_code",
}

#安全除法函数，避免除以零错误
def safe_divide(numerator: int | float, denominator: int | float) -> float | None:
    return None if denominator == 0 else numerator / denominator

#清洗事件数据，处理缺失值、无效日期和重复事件
def clean_events(events: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    missing = REQUIRED_EVENT_COLUMNS - set(events.columns)
    if missing:
        raise ValueError(f"events.csv 缺少字段: {', '.join(sorted(missing))}")
    result = events.copy()
    raw_count = len(result)
    result["event_time"] = pd.to_datetime(result["event_time"], errors="coerce")
    invalid_dates = int(result["event_time"].isna().sum())
    result = result.dropna(subset=["event_time", "event_id", "user_id", "event_name"])
    before_dedupe = len(result)
    result = result.drop_duplicates(subset=["event_id"], keep="first")
    result["error_code"] = result["error_code"].fillna("NO_ERROR").replace("", "NO_ERROR")
    quality = {
        "raw_rows": raw_count,
        "clean_rows": len(result),
        "invalid_date_rows_removed": invalid_dates,
        "duplicate_events_removed": before_dedupe - len(result),
        "deduplication_key": "event_id",
        "metric_grain": "去重用户数（user_id）",
    }
    return result, quality

#按日期范围和活动ID过滤事件数据
def filter_events(events: pd.DataFrame, start_date=None, end_date=None, campaign_ids: Iterable[str] | None = None) -> pd.DataFrame:
    result = events.copy()
    if start_date is not None:
        result = result[result["event_time"].dt.date >= pd.Timestamp(start_date).date()]
    if end_date is not None:
        result = result[result["event_time"].dt.date <= pd.Timestamp(end_date).date()]
    if campaign_ids:
        result = result[result["campaign_id"].isin(campaign_ids)]
    return result


#计算漏斗指标
def compute_funnel(events: pd.DataFrame) -> dict:
    counts = {name: int(events.loc[events["event_name"] == name, "user_id"].nunique()) for name in FUNNEL_EVENTS}
    #统计领取失败用户数
    failures = int(events.loc[events["event_name"] == "coupon_claim_fail", "user_id"].nunique())
    return {
        "exposure_users": counts["exposure"],
        "click_users": counts["click"],
        "claim_users": counts["coupon_claim"],
        "claim_failure_users": failures,
        "ctr": safe_divide(counts["click"], counts["exposure"]),
        "click_to_claim_rate": safe_divide(counts["coupon_claim"], counts["click"]),
        "exposure_to_claim_rate": safe_divide(counts["coupon_claim"], counts["exposure"]),
    }


#按指定维度分组计算漏斗指标
def grouped_funnel(events: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in events.columns:
        raise ValueError(f"未知分组字段: {dimension}")
    rows = []
    for value, group in events.groupby(dimension, dropna=False):
        rows.append({dimension: value if pd.notna(value) else "UNKNOWN", **compute_funnel(group)})
    return pd.DataFrame(rows)


#按错误码统计领取失败原因
def failure_reason_breakdown(events: pd.DataFrame) -> pd.DataFrame:
    failed = events[events["event_name"] == "coupon_claim_fail"]
    if failed.empty:
        return pd.DataFrame(columns=["error_code", "failed_users", "share"])
    result = failed.groupby("error_code")["user_id"].nunique().rename("failed_users").reset_index()
    result["share"] = result["failed_users"] / result["failed_users"].sum()
    return result.sort_values("failed_users", ascending=False).reset_index(drop=True)

#诊断漏斗瓶颈
def diagnose_bottleneck(events: pd.DataFrame) -> dict:
    funnel = compute_funnel(events)
    reasons = failure_reason_breakdown(events)
    if funnel["click_users"] == 0:
        stage = "点击环节"
        evidence = "无点击用户，无法评估点击后的领券转化。"
    elif funnel["click_to_claim_rate"] is not None and funnel["click_to_claim_rate"] < 0.25:
        stage = "点击后领券环节"
        evidence = f"点击到领券转化率仅 {funnel['click_to_claim_rate']:.1%}。"
    else:
        stage = "未发现显著单点瓶颈"
        evidence = "当前规则阈值下，点击到领券转化率未低于 25%。"
    top_reason = None if reasons.empty else reasons.iloc[0].to_dict()
    return {"stage": stage, "evidence": evidence, "funnel": funnel, "top_failure_reason": top_reason}

