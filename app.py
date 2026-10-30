from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from traffic_agent.agent import DiagnosticAgent
from traffic_agent.analytics import compute_funnel, failure_reason_breakdown, filter_events, grouped_funnel
from traffic_agent.data import load_data


ROOT = Path(__file__).parent
st.set_page_config(page_title="AI Agent 流量运营诊断台", page_icon="🚕", layout="wide")
st.title("AI Agent 驱动的端内流量运营与转化提效平台")
st.warning("作品集演示：本项目全部数据均为模拟数据，不来自任何真实业务。分析结论仅用于展示方法。")
#加载缓存数据，缓存函数结果，让相同输入下的数据读取更快
@st.cache_data
def cached_data():
    return load_data(ROOT / "data")

events, campaigns, quality = cached_data()
#侧边栏筛选
with st.sidebar:
    st.header("分析范围")
    min_date, max_date = events["event_time"].min().date(), events["event_time"].max().date()
    date_range = st.date_input("日期范围", (min_date, max_date), min_value=min_date, max_value=max_date)
    campaign_options = campaigns["campaign_id"].tolist()
    selected = st.multiselect("活动", campaign_options, default=campaign_options)
    st.caption("指标口径：event_id 去重后按 user_id 统计去重用户；日期含首尾两日。")
#不完整日期处理
if len(date_range) != 2:
    st.info("请选择完整的开始和结束日期。")
    st.stop()
filtered = filter_events(events, date_range[0], date_range[1], selected)
funnel = compute_funnel(filtered)

tab1, tab2, tab3, tab4 = st.tabs(["漏斗总览", "证据下钻", "Agent 诊断", "数据口径"])
with tab1:
    cols = st.columns(5)
    metrics = [
        ("曝光用户", funnel["exposure_users"]), ("点击用户", funnel["click_users"]),
        ("CTR", funnel["ctr"]), ("成功领券用户", funnel["claim_users"]),
        ("点击→领券", funnel["click_to_claim_rate"]),
    ]
    for col, (name, value) in zip(cols, metrics):
        display = "N/A" if value is None else (f"{value:.1%}" if isinstance(value, float) else f"{value:,}")
        col.metric(name, display)
    funnel_df = pd.DataFrame({"stage": ["曝光", "点击", "成功领券"], "users": [funnel["exposure_users"], funnel["click_users"], funnel["claim_users"]]})
    st.plotly_chart(px.funnel(funnel_df, x="users", y="stage", title="去重用户漏斗"), width="stretch")

with tab2:
    left, right = st.columns(2)
    position_df = grouped_funnel(filtered, "resource_position")
    segment_df = grouped_funnel(filtered, "segment")
    left.plotly_chart(px.bar(position_df, x="resource_position", y=["ctr", "click_to_claim_rate"], barmode="group", title="资源位：高点击是否带来高领券？"), width="stretch")
    right.plotly_chart(px.bar(segment_df, x="segment", y="click_to_claim_rate", title="分群点击后领券率"), width="stretch")
    failures = failure_reason_breakdown(filtered)
    st.plotly_chart(px.bar(failures, x="error_code", y="failed_users", color="share", title="领券失败原因（去重失败用户）"), width="stretch")
    with st.expander("查看明细表"):
        st.dataframe(position_df, width="stretch")
        st.dataframe(segment_df, width="stretch")

with tab3:
    api_available = bool(os.getenv("OPENAI_API_KEY"))
    st.caption("当前模式：" + ("已检测到 API Key，可调用真实模型" if api_available else "未配置 API Key，将使用规则演示模式且不会假装调用模型"))
    if st.button("运行诊断 Agent", type="primary"):
        try:
            report = DiagnosticAgent().run(filtered, campaigns)
        except Exception as exc:
            st.error(f"Agent 运行失败：{exc}")
        else:
            st.success(report.mode)
            st.subheader("事实")
            for item in report.facts: st.markdown(f"- {item.get('statement')}  \n  证据：{item.get('evidence')}")
            st.subheader("假设（待验证）")
            for item in report.hypotheses: st.markdown(f"- {item.get('statement')}  \n  依据/限制：{item.get('evidence')}")
            st.subheader("建议")
            st.dataframe(pd.DataFrame(report.recommendations), width="stretch")
            st.subheader("实验方案")
            st.json(report.experiments)
            st.subheader("监控方案")
            st.dataframe(pd.DataFrame(report.monitoring), width="stretch")
            with st.expander("Agent 工具调用轨迹"): st.write(report.tool_trace)

with tab4:
    st.json(quality)
    st.markdown("**边界说明**：空曝光分母显示 N/A；错误码缺失补为 `NO_ERROR`；无效日期行剔除；重复事件按 `event_id` 保留第一条；未做跨活动归因。")
    st.dataframe(campaigns, width="stretch")

