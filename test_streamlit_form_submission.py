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
    def _enter_complete_form_except_cloth_width(app):
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
            "rem_": 4.5,
            "design_life": 20,
            "df": 0.72,
            "installation_temp": 20.0,
            "cyclic_derating_factor": 1.0,
        }.items():
            app.number_input(key=key).set_value(value)

        app.selectbox(key="type_").select("Corrosion")
        app.selectbox(key="loc_").select("External")
        app.selectbox(key="component_type").select("Straight")
        app.selectbox(key="axial_load_case").select(0)
        app.run()

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
