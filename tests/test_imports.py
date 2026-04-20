"""Smoke tests for the iqflow_wind_sensor app.

Validates imports, schema well-formedness, Tags/UI subclassing, and that
the config/UI export entry points run end-to-end.
"""

import json

from pydoover.config import Schema
from pydoover.tags import Tags
from pydoover.ui import UI


def test_import_app():
    from iqflow_wind_sensor.application import IQFlowWindSensorApplication
    assert IQFlowWindSensorApplication.config_cls is not None
    assert IQFlowWindSensorApplication.tags_cls is not None
    assert IQFlowWindSensorApplication.ui_cls is not None


def test_config_schema():
    from iqflow_wind_sensor.app_config import IQFlowWindSensorConfig
    assert issubclass(IQFlowWindSensorConfig, Schema)

    schema = IQFlowWindSensorConfig.to_schema()
    assert isinstance(schema, dict)
    assert schema["type"] == "object"
    for key in (
        "sensor_name",
        "variant",
        "modbus_config",
        "slave_id",
        "poll_interval_seconds",
        "display_unit",
        "gust_window_seconds",
        "no_comms_timeout_seconds",
    ):
        assert key in schema["properties"], f"{key} missing from config schema"


def test_tags():
    from iqflow_wind_sensor.app_tags import IQFlowWindSensorTags
    assert issubclass(IQFlowWindSensorTags, Tags)


def test_ui():
    from iqflow_wind_sensor.app_ui import IQFlowWindSensorUI
    assert issubclass(IQFlowWindSensorUI, UI)


def test_config_export(tmp_path):
    from iqflow_wind_sensor.app_config import IQFlowWindSensorConfig

    fp = tmp_path / "doover_config.json"
    IQFlowWindSensorConfig.export(fp, "iqflow_wind_sensor")

    data = json.loads(fp.read_text())
    assert "iqflow_wind_sensor" in data
    assert "config_schema" in data["iqflow_wind_sensor"]


def test_ui_export(tmp_path):
    from iqflow_wind_sensor.app_ui import IQFlowWindSensorUI

    fp = tmp_path / "doover_config.json"
    IQFlowWindSensorUI(None, None, None).export(fp, "iqflow_wind_sensor")

    data = json.loads(fp.read_text())
    assert "ui_schema" in data["iqflow_wind_sensor"]
    assert data["iqflow_wind_sensor"]["ui_schema"]["type"] == "uiApplication"
    assert "wind_speed" in data["iqflow_wind_sensor"]["ui_schema"]["children"]
