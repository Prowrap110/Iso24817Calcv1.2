import unittest

from b31g import assess_b31g
from corrosion_defects import (
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
)
from prowrap_calculations import calculate_repair
from test_current_calculation_baseline import default_inputs


class CorrosionDefectModesTest(unittest.TestCase):
    def test_default_mode_keeps_exact_v11_baseline(self):
        result = calculate_repair(**default_inputs())
        self.assertEqual(result["defect_length_basis"], "Actual defect length")
        self.assertEqual(
            result["calculation_basis"],
            "ASME B31G-2023 Level 1 (Modified)",
        )
        self.assertAlmostEqual(result["p_steel_capacity"], 9.951873620726573)
        self.assertAlmostEqual(result["iso_length"], 388.933816016055)

    def test_high_smys_fallback_reports_governing_original_method(self):
        inputs = default_inputs(yield_strength=555.0)
        expected = assess_b31g(
            od_mm=inputs["od"],
            wall_mm=inputs["wall"],
            depth_mm=inputs["wall"] - inputs["rem_wall"],
            length_mm=inputs["length"],
            smys_mpa=inputs["yield_strength"],
            safety_factor=max(1.0 / inputs["design_factor"], 1.25),
            method="modified",
            operating_pressure_mpa=inputs["pressure"] * 0.1,
        )

        result = calculate_repair(**inputs)

        self.assertEqual(expected["method"], "original")
        self.assertAlmostEqual(result["p_steel_capacity"], expected["p_s_mpa"])
        self.assertEqual(result["b31g_details"]["method"], "original")
        self.assertEqual(
            result["calculation_basis"],
            "ASME B31G-2023 Level 1 (Original)",
        )
        self.assertTrue(any(
            "falling back to Original B31G" in warning
            for warning in result["compliance_warnings"]
        ))

    def test_independent_mode_uses_ten_mm_b31g_and_full_zone_coverage(self):
        result = calculate_repair(
            **default_inputs(
                od=1016.0, wall=12.0, pressure=104.9, length=1000.0,
                rem_wall=9.652, yield_strength=450.0,
            ),
            defect_length_basis=INDEPENDENT_DEFECTS,
        )
        expected = assess_b31g(
            od_mm=1016.0, wall_mm=12.0, depth_mm=2.348,
            length_mm=10.0, smys_mpa=450.0,
            safety_factor=max(1.0 / 0.72, 1.25), method="modified",
            operating_pressure_mpa=10.49,
        )
        self.assertAlmostEqual(result["p_steel_capacity"], expected["p_s_mpa"])
        self.assertEqual(result["governing_b31g_length_mm"], 10.0)
        self.assertAlmostEqual(
            result["iso_length"] - 2 * result["overlap_length"]
            - 2 * result["taper_length"],
            1000.0,
        )

    def test_manual_mode_preserves_pairs_and_selects_lowest_credit(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=6.0, wall=12.0),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("LONG", 300.0, 11.0, True),
                IndividualCorrosionDefect("DEEP", 10.0, 6.0, True),
            ),
        )
        items = {item["defect_id"]: item for item in result["b31g_assessments"]}
        self.assertEqual(
            (items["LONG"]["length_mm"], items["LONG"]["remaining_wall_mm"]),
            (300.0, 11.0),
        )
        self.assertEqual(
            (items["DEEP"]["length_mm"], items["DEEP"]["remaining_wall_mm"]),
            (10.0, 6.0),
        )
        self.assertEqual(
            result["p_steel_capacity"],
            min(item["credited_pressure_mpa"] for item in items.values()),
        )

    def test_nonapplicable_manual_candidate_removes_credit(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=0.9),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("SOUND", 10.0, 8.0, True),
                IndividualCorrosionDefect("SEVERE", 10.0, 0.9, True),
            ),
        )
        self.assertEqual(result["governing_defect_id"], "SEVERE")
        self.assertEqual(result["p_steel_capacity"], 0.0)
        self.assertEqual(result["calc_method_thick"], "Type B (Total Replacement)")

    def test_internal_corrosion_ignores_external_only_mode(self):
        result = calculate_repair(
            **default_inputs(defect_loc="Internal", rem_wall=4.5),
            defect_length_basis=INDEPENDENT_DEFECTS,
        )
        self.assertEqual(result["defect_length_basis"], "Actual defect length")
        self.assertEqual(result["calc_method_thick"], "Type B (Total Replacement)")

    def test_equal_manual_credits_keep_first_candidate_as_governing(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=8.0),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("FIRST", 10.0, 8.0, True),
                IndividualCorrosionDefect("SECOND", 10.0, 8.0, True),
            ),
        )
        self.assertEqual(result["governing_defect_id"], "FIRST")

    def test_b31g_inapplicable_candidate_gets_zero_credit_and_traceability(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=1.8),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("SOUND", 10.0, 8.0, True),
                IndividualCorrosionDefect("OUTSIDE-B31G", 10.0, 1.8, True),
            ),
        )
        items = {item["defect_id"]: item for item in result["b31g_assessments"]}
        self.assertFalse(items["OUTSIDE-B31G"]["assessment"]["applicable"])
        self.assertEqual(items["OUTSIDE-B31G"]["credited_pressure_mpa"], 0.0)
        self.assertEqual(result["governing_defect_id"], "OUTSIDE-B31G")
        self.assertEqual(result["p_steel_capacity"], 0.0)
        self.assertEqual(
            result["calculation_basis"],
            "ASME B31G-2023 Level 1 (Modified; outside applicability)",
        )

    def test_candidate_warnings_include_defect_ids_and_no_exact_duplicates(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=9.0),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("LOW-LOSS-A", 10.0, 9.0, True),
                IndividualCorrosionDefect("LOW-LOSS-B", 12.0, 9.0, True),
            ),
        )
        warnings = result["compliance_warnings"]
        self.assertTrue(
            any(warning.startswith("Defect ID LOW-LOSS-A:") for warning in warnings)
        )
        self.assertTrue(
            any(warning.startswith("Defect ID LOW-LOSS-B:") for warning in warnings)
        )
        self.assertEqual(len(warnings), len(set(warnings)))


if __name__ == "__main__":
    unittest.main()
