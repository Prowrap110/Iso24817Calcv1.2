"""Pure form state helpers for the Streamlit calculator."""

NEUTRAL_CHOICE = "Select…"

INPUT_DEFAULTS = {
    "customer": "",
    "location": "",
    "report_no": "",
    "od": None,
    "wall": None,
    "yield_str": None,
    "pres": None,
    "temp": None,
    "type_": NEUTRAL_CHOICE,
    "loc_": NEUTRAL_CHOICE,
    "len_": None,
    "rem_": None,
    "corr_rate": None,
    "design_life": None,
    "df": None,
    "show_typea_class3_check": False,
    "installation_temp": None,
    "component_type": NEUTRAL_CHOICE,
    "cyclic_derating_factor": None,
    "axial_load_case": None,
    "cloth_width_mm": None,
}


def initialise_inputs(state):
    """Add missing blank input values without overwriting entered values."""
    for key, value in INPUT_DEFAULTS.items():
        state.setdefault(key, value)


def new_calculation(state):
    """Clear user-entered inputs and any displayed calculation result state."""
    for key, value in INPUT_DEFAULTS.items():
        state[key] = value
    state["calc_active"] = False
    state["force_3_layers"] = False


def inputs_are_complete(values):
    """Return whether the common required fields contain usable data."""
    required = (
        "customer", "location", "report_no", "od", "wall", "yield_str", "pres",
        "temp", "type_", "loc_", "len_", "rem_", "design_life", "df",
        "installation_temp", "component_type", "cyclic_derating_factor",
        "axial_load_case", "cloth_width_mm",
    )
    for key in required:
        value = values.get(key)
        if value is None or value == "" or value == NEUTRAL_CHOICE:
            return False
    if values.get("type_") == "Corrosion" and values.get("loc_") == "Internal":
        return values.get("corr_rate") is not None
    return True
