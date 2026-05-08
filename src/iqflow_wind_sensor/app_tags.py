from pydoover.tags import Tags, Number, Boolean, String, Delta, AnyChange


class IQFlowWindSensorTags(Tags):
    wind_speed = Number(default=0, log_on=Delta(amount=20))
    wind_gust = Number(default=0, log_on=Delta(amount=20))
    wind_direction_degrees = Number(default=0, log_on=Delta(amount=90))
    wind_direction_compass = String(default="", log_on=AnyChange())

    # ---- comms / diagnostics --------------------------------------------
    comms_ok = Boolean(default=False, log_on=AnyChange())
    last_read_time = Number(default=0)

    # Raw register values (diagnostics / audit).
    raw_speed_value = Number(default=0)
    raw_direction_index = Number(default=0)

    # ---- technician command tags (no UI; tag-only per design) -----------
    # Set one of these to a non-null value to trigger a Modbus write.
    # The app clears the tag back to None after executing and populates
    # last_cmd_result. Default=None so `is not None` reliably filters out
    # unset tags (a Tag with no default reads as the NotSet sentinel).
    cmd_set_slave_id = Number(default=None)
    cmd_set_baud = Number(default=None)
    cmd_set_parity = String(default=None)
    last_cmd_result = String(default="", log_on=AnyChange())
