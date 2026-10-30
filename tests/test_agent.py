from traffic_agent.agent import DiagnosticAgent


def test_demo_mode_is_explicit_and_report_has_required_sections(sample_bundle):
    events, campaigns = sample_bundle
    result = DiagnosticAgent(api_key=None).run(events, campaigns)
    assert result.mode == "规则演示模式（未调用真实模型）"
    assert result.facts
    assert result.hypotheses
    assert result.recommendations
    assert result.experiments
    assert result.monitoring
    assert all(item.get("evidence") for item in result.facts)


def test_agent_rejects_unsupported_model_provider(sample_bundle):
    events, campaigns = sample_bundle
    agent = DiagnosticAgent(api_key="secret", provider="unsupported")
    try:
        agent.run(events, campaigns)
    except ValueError as exc:
        assert "provider" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")

