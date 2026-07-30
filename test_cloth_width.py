import unittest

from prowrap_calculations import calculate_repair
from test_current_calculation_baseline import default_inputs


class ClothWidthTest(unittest.TestCase):
    def test_300_mm_width_preserves_baseline_procurement(self):
        result = calculate_repair(**default_inputs(), cloth_width_mm=300.0)

        self.assertEqual(result["num_bands"], 2)
        self.assertEqual(result["proc_length"], 600.0)
        self.assertAlmostEqual(result["optimized_sqm"], 2.585405090198256)

    def test_width_changes_procurement_without_changing_structural_plies(self):
        at_300 = calculate_repair(**default_inputs(), cloth_width_mm=300.0)
        at_250 = calculate_repair(**default_inputs(), cloth_width_mm=250.0)

        self.assertEqual(at_250["num_plies"], at_300["num_plies"])
        self.assertEqual(at_250["final_thickness"], at_300["final_thickness"])
        self.assertEqual(at_250["num_bands"], 2)
        self.assertEqual(at_250["proc_length"], 500.0)
        self.assertNotEqual(at_250["optimized_sqm"], at_300["optimized_sqm"])

    def test_width_must_exceed_qualified_stitch_overlap(self):
        for width in (0.0, 49.0, 50.0):
            with self.subTest(width=width):
                with self.assertRaisesRegex(ValueError, "cloth width"):
                    calculate_repair(**default_inputs(), cloth_width_mm=width)


if __name__ == "__main__":
    unittest.main()
