from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from traffic_agent.agent import DiagnosticAgent
from traffic_agent.analytics import compute_funnel
from traffic_agent.data import load_data


events, campaigns, quality = load_data(root / "data")
funnel = compute_funnel(events)
report = DiagnosticAgent(api_key=None).run(events, campaigns)
assert funnel["exposure_users"] > 0
assert funnel["click_users"] > 0
assert report.mode.startswith("规则演示模式")
assert report.facts and report.experiments and report.monitoring
print("SELF_CHECK_OK")
print({"events": len(events), "campaigns": len(campaigns), "quality": quality, "funnel": funnel, "agent_mode": report.mode})

