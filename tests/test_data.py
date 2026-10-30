from pathlib import Path

from traffic_agent.data import load_data


def test_shipped_simulated_data_loads_and_reports_quality():
    events, campaigns, quality = load_data(Path(__file__).parents[1] / "data")
    assert not events.empty
    assert not campaigns.empty
    assert quality["duplicate_events_removed"] >= 1
    assert quality["invalid_date_rows_removed"] >= 1

