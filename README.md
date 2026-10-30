# AI Agent 驱动的端内流量运营与转化提效平台

面向流量运营实习作品集的可运行演示项目。核心业务问题是：**为什么首页 Banner 点击率高，但领券转化率低？**

> 数据声明：仓库中的 `events.csv` 与 `campaigns.csv` 全部由脚本随机生成，是明确标注的模拟数据，不来自滴滴或任何真实业务。本项目不声称已部署、已上线或带来真实转化提升。

## 能力概览

- 去重用户漏斗：曝光、点击、成功领券，安全处理空分母
- 资源位对比、用户分群、领券失败错误码下钻
- 数据质量：无效日期、重复事件、缺失错误码、日期边界与字段校验
- Agent 编排：调用 Python 分析工具，输出事实 / 假设 / 建议 / 实验 / 监控
- 双模式：无 Key 时透明使用规则演示模式；配置 Key 后调用 OpenAI Responses API
- Streamlit 交互页面与 Plotly 图表

## 数据字段

`events.csv`：`event_id`、`user_id`、`event_time`、`event_name`、`campaign_id`、`resource_position`、`segment`、`error_code`。

`campaigns.csv`：`campaign_id`、`campaign_name`、`budget`、`coupon_stock`。

事件类型为 `exposure`、`click`、`coupon_claim`、`coupon_claim_fail`。核心指标按 `event_id` 去重后，以 `user_id` 去重人数计算。日期筛选包含开始日和结束日。曝光分母为 0 时返回 `N/A`，不会错误展示为 0%。

## 本地运行

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\generate_simulated_data.py
streamlit run app.py
```

浏览器通常会打开 `http://localhost:8501`。

## 模型配置（可选）

不配置任何 Key 即可完整演示，页面会明确显示“规则演示模式（未调用真实模型）”。如需调用真实模型：

```powershell
$env:OPENAI_API_KEY="你的密钥"
$env:OPENAI_MODEL="gpt-4.1-mini"
streamlit run app.py
```

应用不会把 Key 写入文件。模型模式要求模型返回指定 JSON；解析失败时会明确报错，不会回退后假装调用成功。

## 测试与自检

```powershell
python -m pytest -q
python scripts\self_check.py
python -m streamlit run app.py --server.headless true
```

最后一条用于启动检查，看到服务地址后可按 `Ctrl+C` 停止。

## 项目结构

```text
app.py                         Streamlit 页面
traffic_agent/analytics.py     数据清洗、漏斗、分群、失败原因与瓶颈工具
traffic_agent/agent.py         Agent 编排、规则模式与真实模型接口
traffic_agent/data.py          CSV 读取与字段校验
data/                          明确标注的模拟 CSV
scripts/generate_simulated_data.py  可复现模拟数据生成
scripts/self_check.py          应用核心链路自检
tests/                         分析口径、边界和 Agent 行为测试
```

## 分析边界

- 这是作品集方法演示，不构成真实业务结论。
- 模拟数据仅展示“首页 Banner 高 CTR、低点击后领券率”的可诊断模式。
- 当前归因按活动与事件直接关联，未处理多触点归因、跨端登录、曝光可见性和实验显著性计算。
- 建议均需在真实业务中结合券规则、库存日志、页面性能与实验数据验证。

