from pathlib import Path
import random

import pandas as pd


random.seed(42)
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

campaigns = pd.DataFrame([
    {"campaign_id": "c001", "campaign_name": "早高峰通勤券", "budget": 50000, "coupon_stock": 3000},
    {"campaign_id": "c002", "campaign_name": "周末出游券", "budget": 35000, "coupon_stock": 2200},
])
campaigns.to_csv(DATA / "campaigns.csv", index=False, encoding="utf-8-sig")

rows = []
event_no = 0
#设置资源位的转化概率（点击率和领取率）
positions = [("首页Banner", 0.38, 0.16), ("金刚位", 0.22, 0.34), ("消息中心", 0.15, 0.29)]
segments = ["新用户", "活跃用户", "沉默召回"]
error_codes = ["OUT_OF_STOCK", "NOT_ELIGIBLE", "COUPON_EXPIRED", "SYSTEM_BUSY"]

#定义添加事件行的函数
def add(user, time, name, campaign, position, segment, error="NO_ERROR"):
    global event_no
    event_no += 1
    rows.append({"event_id": f"evt_{event_no:06d}", "user_id": user, "event_time": time, "event_name": name, "campaign_id": campaign, "resource_position": position, "segment": segment, "error_code": error})

#模拟用户行为
for day in pd.date_range("2026-09-01", "2026-09-14"):
    for n in range(180):
        user = f"u_{day.day:02d}_{n:03d}"
        position, click_rate, claim_rate = random.choice(positions)
        #模拟用户访问资源位
        segment = random.choice(segments)
        campaign = random.choice(["c001", "c002"])
        t = day + pd.Timedelta(minutes=random.randint(0, 1439))
        #模拟曝光事件
        add(user, t, "exposure", campaign, position, segment)
        #模拟点击事件
        if random.random() < click_rate:
            add(user, t + pd.Timedelta(seconds=12), "click", campaign, position, segment)
            adjusted_claim = claim_rate * (0.65 if segment == "沉默召回" else 1)
            #模拟领取事件
            if random.random() < adjusted_claim:
                add(user, t + pd.Timedelta(seconds=28), "coupon_claim", campaign, position, segment)
            else:
                #模拟领取失败事件
                weights = [0.48, 0.30, 0.14, 0.08] if position == "首页Banner" else [0.25, 0.38, 0.22, 0.15]
                add(user, t + pd.Timedelta(seconds=28), "coupon_claim_fail", campaign, position, segment, random.choices(error_codes, weights=weights)[0])
#添加异常数据行（重复行和无效日期行）
rows.append(rows[0].copy())
bad = rows[1].copy(); bad["event_id"] = "evt_bad_date"; bad["event_time"] = "invalid-date"; rows.append(bad)
pd.DataFrame(rows).to_csv(DATA / "events.csv", index=False, encoding="utf-8-sig")
print(f"Generated {len(rows)} explicitly simulated event rows in {DATA}")

