import unittest

from calculator_form import (
    INPUT_DEFAULTS,
    calculation_corrosion_rate,
    inputs_are_complete,
    missing_required_fields,
    new_calculation,
)


class CalculatorFormTest(unittest.TestCase):
    def test_new_calculation_clears_entered_values_and_results(self):
        state = {key: "entered" for key in INPUT_DEFAULTS}
        state.update({"calc_active": True, "force_3_layers": True})

        new_calculation(state)

        self.assertEqual(
            {key: state[key] for key in INPUT_DEFAULTS}, INPUT_DEFAULTS
        )
        self.assertFalse(state["calc_active"])
        self.assertFalse(state["force_3_layers"])

    def test_blank_form_is_not_ready_to_calculate(self):
        self.assertFalse(inputs_are_complete(INPUT_DEFAULTS))

    def test_complete_form_is_ready_to_calculate(self):
        values = dict(INPUT_DEFAULTS)
        values.update(
            {
                "customer": "PROTAP",
                "location": "Turkey",
                "report_no": "26-001",
                "od": 457.2,
                "wall": 9.53,
                "yield_str": 359.0,
                "pres": 50.0,
                "temp": 40.0,
                "type_": "Corrosion",
                "loc_": "External",
                "len_": 100.0,
                "rem_": 4.5,
                "design_life": 20,
                "df": 0.72,
                "show_typea_class3_check": True,
                "installation_temp": 20.0,
                "component_type": "Straight",
                "cyclic_derating_factor": 1.0,
                "axial_load_case": 0,
                "cloth_width_mm": 300.0,
            }
        )

        self.assertTrue(inputs_are_complete(values))

    def test_missing_required_fields_uses_user_facing_labels(self):
        values = dict(INPUT_DEFAULTS)
        values.update(
            {
                "customer": "PROTAP",
                "location": "Turkey",
                "report_no": "26-001",
                "od": 457.2,
                "wall": 9.53,
                "yield_str": 359.0,
                "pres": 50.0,
                "temp": 40.0,
                "type_": "Corrosion",
                "loc_": "External",
                "len_": 100.0,
                "rem_": 4.5,
                "design_life": 20,
                "df": 0.72,
                "installation_temp": 20.0,
                "component_type": "Straight",
                "cyclic_derating_factor": 1.0,
                "axial_load_case": 0,
            }
        )

        self.assertEqual(
            missing_required_fields(values),
            ["Prowrap CF cloth band width [mm]"],
        )

    def test_internal_corrosion_requires_an_explicit_corrosion_rate(self):
        values = dict(INPUT_DEFAULTS)
        values.update(
            {
                "customer": "PROTAP", "location": "Turkey", "report_no": "26-001",
                "od": 457.2, "wall": 9.53, "yield_str": 359.0, "pres": 50.0,
                "temp": 40.0, "type_": "Corrosion", "loc_": "Internal",
                "len_": 100.0, "rem_": 4.5, "design_life": 20, "df": 0.72,
                "installation_temp": 20.0, "component_type": "Straight",
                "cyclic_derating_factor": 1.0, "axial_load_case": 0,
                "cloth_width_mm": 300.0,
            }
        )

        self.assertFalse(inputs_are_complete(values))
        self.assertEqual(
            missing_required_fields(values),
            ["Internal Corrosion Rate [mm/yr]"],
        )
        values["corr_rate"] = 0.0
        self.assertTrue(inputs_are_complete(values))
        self.assertEqual(missing_required_fields(values), [])

    def test_non_internal_corrosion_uses_zero_rate_when_field_is_blank(self):
        values = dict(INPUT_DEFAULTS)
        values.update({"type_": "Corrosion", "loc_": "External"})

        self.assertEqual(calculation_corrosion_rate(values), 0.0)


if __name__ == "__main__":
    unittest.main()
