import pytest

from prowrap_calculations import (
    calculate_repair,
    component_pipe_allowable_basis,
    substrate_credit_bar_for_iso_check,
)
from prowrap_mechanisms import MECHANISM_CHOICES, normalize_mechanism
from test_current_calculation_baseline import default_inputs


def test_canonical_mechanism_choices_replace_generic_dent():
    assert MECHANISM_CHOICES == (
        "Corrosion", "Dent w/crack", "Dent no-crack", "Leak", "Crack",
    )
    assert "Dent" not in MECHANISM_CHOICES
    assert normalize_mechanism(" Dent no-crack ") == "Dent no-crack"
    with pytest.raises(ValueError, match="Unsupported defect mechanism"):
        normalize_mechanism("Dent")


def test_component_pipe_allowable_basis_uses_approved_equation():
    basis = component_pipe_allowable_basis(
        od_mm=457.2,
        remaining_wall_mm=9.53,
        smys_mpa=359.0,
        design_factor=0.72,
    )
    expected_stress = 359.0 * 0.72
    expected_pressure = 2.0 * expected_stress * 9.53 / 457.2
    assert basis["allowable_stress_mpa"] == pytest.approx(expected_stress)
    assert basis["allowable_pressure_mpa"] == pytest.approx(expected_pressure)


def test_dent_with_crack_preserves_current_full_pressure_result():
    result = calculate_repair(**default_inputs(
        defect_type="Dent w/crack", rem_wall=9.53,
    ))
    assert result["calculation_basis"] == (
        "Dent w/crack - full-pressure laminate"
    )
    assert result["allowable_pipe_stress_mpa"] is None
    assert result["p_steel_capacity"] == 0.0
    assert result["p_composite_design"] == 5.0
    assert result["t_required"] == pytest.approx(7.4240889243)
    assert result["num_plies"] == 9
    assert result["final_thickness"] == pytest.approx(7.47)
    assert substrate_credit_bar_for_iso_check(result) == 0.0


def test_external_dent_no_crack_uses_component_pipe_load_sharing():
    result = calculate_repair(**default_inputs(
        defect_type="Dent no-crack", rem_wall=9.53,
    ))
    expected_stress = 359.0 * 0.72
    expected_pressure = 2.0 * expected_stress * 9.53 / 457.2
    assert result["calculation_basis"] == (
        "Dent no-crack - substrate load sharing"
    )
    assert result["allowable_pipe_stress_mpa"] == pytest.approx(expected_stress)
    assert result["p_steel_capacity"] == pytest.approx(expected_pressure)
    assert result["p_composite_design"] == 0.0
    assert result["typea_design"]["tmin_c_mm"] == 0.0
    assert result["num_plies"] == 3
    assert result["final_thickness"] == pytest.approx(2.49)
    assert substrate_credit_bar_for_iso_check(result) == pytest.approx(
        expected_pressure * 10.0
    )


@pytest.mark.parametrize("mechanism", ["Dent w/crack", "Dent no-crack"])
@pytest.mark.parametrize(
    ("location", "remaining_wall"),
    [("Internal", 9.53), ("External", 0.9)],
)
def test_dent_routes_without_eligible_substrate_are_type_b(
    mechanism, location, remaining_wall,
):
    result = calculate_repair(**default_inputs(
        defect_type=mechanism,
        defect_loc=location,
        rem_wall=remaining_wall,
    ))
    assert result["calc_method_thick"] == "Type B (Total Replacement)"
    assert result["p_steel_capacity"] == 0.0
    assert result["allowable_pipe_stress_mpa"] is None


def test_dent_no_crack_formula5_receives_only_the_pressure_deficit():
    result = calculate_repair(**default_inputs(
        defect_type="Dent no-crack",
        rem_wall=3.0,
        pressure=120.0,
    ))
    expected_ps = 2.0 * (359.0 * 0.72) * 3.0 / 457.2
    assert result["p_steel_capacity"] == pytest.approx(expected_ps)
    assert result["p_composite_design"] == pytest.approx(12.0 - expected_ps)
    assert result["typea_design"]["substrate_pressure_mpa"] == pytest.approx(
        expected_ps
    )
    assert result["typea_design"]["tmin_c_mm"] > 0.0
