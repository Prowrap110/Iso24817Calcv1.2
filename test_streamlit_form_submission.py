import unittest

try:
    from streamlit.testing.v1 import AppTest
except ModuleNotFoundError:
    AppTest = None


@unittest.skipUnless(AppTest, "Streamlit AppTest requires the desktop environment")
class StreamlitFormSubmissionTest(unittest.TestCase):
    @staticmethod
    def _calculate_button(app):
        return next(
            button for button in app.button
            if button.label == "Calculate & Optimize"
        )

    @staticmethod
    def _enter_complete_form_except_cloth_width(
        app, mechanism="Corrosion", remaining_wall=4.5,
    ):
        for key, value in {
            "customer": "PROTAP",
            "location": "Turkey",
            "report_no": "26-001",
        }.items():
            app.text_input(key=key).set_value(value)

        for key, value in {
            "od": 457.2,
            "wall": 9.53,
            "yield_str": 359.0,
            "pres": 50.0,
            "temp": 40.0,
            "len_": 100.0,
            "rem_": remaining_wall,
            "design_life": 20,
            "df": 0.72,
            "installation_temp": 20.0,
            "cyclic_derating_factor": 1.0,
        }.items():
            app.number_input(key=key).set_value(value)

        app.selectbox(key="type_").select(mechanism)
        app.selectbox(key="loc_").select("External")
        app.selectbox(key="component_type").select("Straight")
        app.selectbox(key="axial_load_case").select(0)
        app.run()

    @staticmethod
    def _rendered_markdown(app):
        return "\n".join(element.value for element in app.markdown)

    def test_mechanism_selector_uses_the_two_canonical_dent_choices(self):
        app = AppTest.from_file("PWR110Calculator.py").run()

        mechanism = app.selectbox(key="type_")

        self.assertEqual(
            mechanism.options,
            [
                "Select…",
                "Corrosion",
                "Dent w/crack",
                "Dent no-crack",
                "Leak",
                "Crack",
            ],
        )
        self.assertNotIn("Dent", mechanism.options)

    def test_dent_with_crack_displays_full_pressure_laminate_basis(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app, mechanism="Dent w/crack", remaining_wall=9.53,
        )
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()

        rendered = self._rendered_markdown(app)
        self.assertEqual(list(app.exception), [])
        self.assertIn("**Mechanism:** Dent w/crack", rendered)
        self.assertIn(
            "**Calculation Basis:** Dent w/crack - full-pressure laminate",
            rendered,
        )
        self.assertIn(
            "**Substrate Allowable Pressure p_s:** 0.00 MPa (0.00 bar)",
            rendered,
        )
        self.assertIn("**Composite Pressure Deficit:** 5.00 MPa", rendered)
        self.assertEqual(app.metric[0].value, "9")

    def test_external_dent_no_crack_displays_substrate_load_sharing_basis(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app, mechanism="Dent no-crack", remaining_wall=9.53,
        )
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()

        rendered = self._rendered_markdown(app)
        self.assertEqual(list(app.exception), [])
        self.assertIn("**Mechanism:** Dent no-crack", rendered)
        self.assertIn(
            "**Calculation Basis:** Dent no-crack - substrate load sharing",
            rendered,
        )
        self.assertIn("**Allowable Pipe Stress S_allow:** 258.48 MPa", rendered)
        self.assertIn(
            "**Substrate Allowable Pressure p_s:** 10.78 MPa (107.76 bar)",
            rendered,
        )
        self.assertIn("**Composite Pressure Deficit:** 0.00 MPa", rendered)
        self.assertEqual(app.metric[0].value, "3")

    def test_incomplete_calculate_is_actionable_and_reports_exact_missing_fields(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(app)

        calculate = self._calculate_button(app)
        self.assertFalse(calculate.disabled)
        self.assertEqual(calculate.proto.type, "secondary")
        self.assertIn(
            "After entering the last value, press Enter or Tab to apply it before calculating.",
            [caption.value for caption in app.caption],
        )

        calculate.click().run()

        self.assertFalse(app.session_state["calc_active"])
        self.assertEqual(
            [error.value for error in app.error],
            ["Missing required fields: Prowrap CF cloth band width [mm]."],
        )

        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self.assertEqual(self._calculate_button(app).proto.type, "primary")
        self._calculate_button(app).click().run()
        self.assertTrue(app.session_state["calc_active"])
        self.assertEqual(list(app.exception), [])


if __name__ == "__main__":
    unittest.main()
