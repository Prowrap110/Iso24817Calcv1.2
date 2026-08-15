import unittest

from prowrap_calculations import calculate_repair
from test_current_calculation_baseline import default_inputs


class InputValidationTest(unittest.TestCase):
    def assert_invalid(self, **overrides):
        with self.assertRaises(ValueError):
            calculate_repair(**default_inputs(**overrides))

    def test_accepts_temperature_at_tg_minus_20_limit(self):
        result = calculate_repair(**default_inputs(temp=90.0))

        self.assertEqual(result["temp"], 90.0)

    def test_rejects_temperature_above_tg_minus_20_limit(self):
        self.assert_invalid(temp=90.01)

    def test_rejects_remaining_wall_greater_than_nominal(self):
        self.assert_invalid(rem_wall=10.0)

    def test_rejects_zero_wall(self):
        self.assert_invalid(wall=0)

    def test_rejects_zero_od(self):
        self.assert_invalid(od=0)

    def test_rejects_negative_pressure(self):
        self.assert_invalid(pressure=-1)

    def test_rejects_invalid_design_factor(self):
        self.assert_invalid(design_factor=0)
        self.assert_invalid(design_factor=1.1)

    def test_rejects_unsupported_defect_locations(self):
        for defect_loc in (None, "", "Unknown", "external"):
            with self.subTest(defect_loc=defect_loc):
                with self.assertRaisesRegex(
                    ValueError, "Unsupported defect location"
                ):
                    calculate_repair(**default_inputs(
                        defect_type="Dent no-crack",
                        defect_loc=defect_loc,
                    ))


if __name__ == "__main__":
    unittest.main()
