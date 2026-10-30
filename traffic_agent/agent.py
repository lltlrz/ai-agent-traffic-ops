from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

import pandas as pd

from .analytics import diagnose_bottleneck, failure_reason_breakdown, grouped_funnel

#定义诊断报告数据类
@dataclass
class DiagnosticReport:
    mode: str
    facts: list[dict]
    hypotheses: list[dict]
    recommendations: list[dict]
    experiments: list[dict]
    monitoring: list[dict]
    tool_trace: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


class DiagnosticAgent:
    """Tool-calling-style orchestrator with transparent rule and optional OpenAI modes."""

    def __init__(self, api_key: str | None = None, provider: str = "openai", model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.provider = provider
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    #初始化诊断代理，设置 API Key、模型提供者和模型名称
    def run(self, events: pd.DataFrame, campaigns: pd.DataFrame) -> DiagnosticReport:
        if self.api_key and self.provider != "openai":
            raise ValueError(f"Unsupported model provider: {self.provider}")
        evidence = self._collect_evidence(events)
        if not self.api_key:
            return self._rule_report(evidence)
        return self._model_report(evidence, campaigns)
    #运行诊断代理，根据事件数据和活动数据生成诊断报告
    def _collect_evidence(self, events: pd.DataFrame) -> dict:
        return {
            "bottleneck": diagnose_bottleneck(events),
            "positions": grouped_funnel(events, "resource_position").to_dict("records"),
            "segments": grouped_funnel(events, "segment").to_dict("records"),
            "failures": failure_reason_breakdown(events).to_dict("records"),
        }
    #收集诊断所需的证据数据
    def _rule_report(self, evidence: dict) -> DiagnosticReport:
        b = evidence["bottleneck"]
        funnel = b["funnel"]
        facts = [
            {"statement": b["evidence"], "evidence": f"去重用户口径：曝光 {funnel['exposure_users']}、点击 {funnel['click_users']}、成功领券 {funnel['claim_users']}。"},
        ]
        top = b["top_failure_reason"]
        if top:
            facts.append({"statement": f"领券失败首要错误码为 {top['error_code']}。", "evidence": f"失败用户 {int(top['failed_users'])}，占全部失败用户 {top['share']:.1%}。"})
        hypotheses = [
            {"statement": "高点击可能来自 Banner 文案吸引，但优惠门槛或库存承接不足。", "evidence": "这是待验证假设，不能由点击与领券事件直接证明。"},
            {"statement": "不同用户分群可能面对不匹配的券门槛。", "evidence": "需结合分群转化差异和券规则进一步验证。"},
        ]
        recommendations = [
            {"action": "优先修复失败占比最高的错误码对应链路", "evidence": f"当前首要错误码：{top['error_code'] if top else '无失败记录'}", "priority": "P0"},
            {"action": "让 Banner 文案明确券门槛、有效期与适用范围", "evidence": "用于降低点击后的预期落差，需通过实验验证", "priority": "P1"},
        ]
        experiments = [{"name": "Banner 信息透明度 A/B", "control": "原 Banner", "treatment": "展示门槛与库存状态", "primary_metric": "点击到成功领券率", "guardrails": ["CTR", "投诉率", "领券失败率"], "duration": "至少 7 天并覆盖工作日/周末"}]
        monitoring = [
            {"metric": "点击到成功领券率", "alert": "较 7 日移动基线下降 20%", "frequency": "小时"},
            {"metric": "领券失败率及错误码分布", "alert": "单一错误码占比 > 40%", "frequency": "小时"},
            {"metric": "资源位 CTR", "alert": "空曝光分母时标记 N/A，不计算 0%", "frequency": "日"},
        ]
        return DiagnosticReport("规则演示模式（未调用真实模型）", facts, hypotheses, recommendations, experiments, monitoring, ["diagnose_bottleneck", "grouped_funnel(resource_position)", "grouped_funnel(segment)", "failure_reason_breakdown"])
    #生成规则演示模式的诊断报告
    def _model_report(self, evidence: dict, campaigns: pd.DataFrame) -> DiagnosticReport:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("已配置 API Key，但未安装 openai 依赖。请运行 pip install -r requirements.txt") from exc
        client = OpenAI(api_key=self.api_key)
        prompt = {
            "task": "仅基于工具证据生成诊断。事实、假设、建议必须分开；不得编造滴滴真实数据。返回 JSON。",
            "required_keys": ["facts", "hypotheses", "recommendations", "experiments", "monitoring"],
            "evidence": evidence,
            "campaigns": campaigns.to_dict("records"),
        }
        response = client.responses.create(model=self.model, input=json.dumps(prompt, ensure_ascii=False))
        try:
            data = json.loads(response.output_text)
        except (json.JSONDecodeError, AttributeError) as exc:
            raise RuntimeError("模型未返回有效 JSON；请切换规则演示模式或检查模型配置。") from exc
        return DiagnosticReport("真实模型模式（OpenAI API）", data["facts"], data["hypotheses"], data["recommendations"], data["experiments"], data["monitoring"], ["Python evidence tools", f"OpenAI Responses API: {self.model}"])

