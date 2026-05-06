from pydoover.tags import Tag, Tags, Number, Boolean


class IQFlowWindSensorTags(Tags):
    # ---- live readings (display unit; see config.display_unit) ----------
    wind_speed = Number(default=0, log_on_cross=1.0)
    wind_gust = Number(default=0)
    wind_direction_degrees = Number(default=0)
    wind_direction_compass = Tag("string", default="")

    # ---- comms / diagnostics --------------------------------------------
    comms_ok = Boolean(default=False, log_on_change=True)
    last_read_time = Number(default=0)

    # Raw register values (diagnostics / audit).
    raw_speed_value = Tag("integer", default=0)
    raw_direction_index = Tag("integer", default=0)

    # ---- technician command tags (no UI; tag-only per design) -----------
    # Set one of these to a non-null value to trigger a Modbus write.
    # The app clears the tag back to None after executing and populates
    # last_cmd_result. Default=None so `is not None` reliably filters out
    # unset tags (a Tag with no default reads as the NotSet sentinel).
    cmd_set_slave_id = Tag("integer", default=None)
    cmd_set_baud = Tag("integer", default=None)
    cmd_set_parity = Tag("string", default=None)
    last_cmd_result = Tag("string", default="")
