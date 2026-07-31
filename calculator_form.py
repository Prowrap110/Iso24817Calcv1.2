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

REQUIRED_FIELD_LABELS = (
    ("customer", "Customer"),
    ("location", "Location"),
    ("report_no", "Report No"),
    ("od", "Pipe OD [mm]"),
    ("wall", "Nominal Wall [mm]"),
    ("yield_str", "Pipe Yield [MPa]"),
    ("pres", "Design Pressure [bar]"),
    ("temp", "Op. Temperature [°C]"),
    ("type_", "Mechanism"),
    ("loc_", "Location"),
    ("len_", "Defect Length [mm]"),
    ("rem_", "Remaining Wall [mm]"),
    ("design_life", "Design Life [years]"),
    ("df", "Design Factor (f)"),
    ("installation_temp", "Installation temperature [°C]"),
    ("component_type", "Component type"),
    ("cyclic_derating_factor", "Cyclic derating factor"),
    ("axial_load_case", "Axial load case"),
    ("cloth_width_mm", "Prowrap CF cloth band width [mm]"),
)


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


def missing_required_fields(values):
    """Return the visible labels for required fields that have no usable value."""
    missing = []
    for key, label in REQUIRED_FIELD_LABELS:
        value = values.get(key)
        if value is None or value == "" or value == NEUTRAL_CHOICE:
            missing.append(label)
    if (
        values.get("type_") == "Corrosion"
        and values.get("loc_") == "Internal"
        and values.get("corr_rate") is None
    ):
        missing.append("Internal Corrosion Rate [mm/yr]")
    return missing


def inputs_are_complete(values):
    """Return whether all required fields contain usable data."""
    return not missing_required_fields(values)


def calculation_corrosion_rate(values):
    """Provide zero post-repair corrosion growth when the optional input is absent."""
    value = values.get("corr_rate")
    return 0.0 if value is None else value
