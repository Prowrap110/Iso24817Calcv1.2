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
        app,
        mechanism="Corrosion",
        remaining_wall=4.5,
        defect_length_basis="Actual defect length",
        od=457.2,
        wall=9.53,
        defect_length=100.0,
    ):
        for key, value in {
            "customer": "PROTAP",
            "location": "Turkey",
            "report_no": "26-001",
        }.items():
            app.text_input(key=key).set_value(value)

        for key, value in {
            "od": od,
            "wall": wall,
            "yield_str": 359.0,
            "pres": 50.0,
            "temp": 40.0,
            "len_": defect_length,
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
        if mechanism == "Corrosion":
            app.selectbox(key="defect_length_basis").select(
                defect_length_basis
            ).run()

    @staticmethod
    def _rendered_markdown(app):
        elements = [*app.markdown, *app.info]
        return "\n".join(element.value for element in elements)

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

    def test_external_corrosion_shows_exact_three_basis_options(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        app.selectbox(key="type_").select("Corrosion")
        app.selectbox(key="loc_").select("External").run()
        self.assertEqual(app.selectbox(key="defect_length_basis").options, [
            "Select…", "Actual defect length", "Independent defects",
            "Enter manually",
        ])

    def test_dent_does_not_show_corrosion_basis(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        app.selectbox(key="type_").select("Dent no-crack")
        app.selectbox(key="loc_").select("External").run()
        self.assertEqual(
            [box for box in app.selectbox if box.key == "defect_length_basis"],
            [],
        )

    def test_independent_mode_shows_assumptions_and_governing_dimensions(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app,
            defect_length_basis="Independent defects",
            od=1016.0,
            wall=12.0,
            remaining_wall=9.652,
            defect_length=1000.0,
        )
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()

        rendered = self._rendered_markdown(app)
        self.assertIn("**Defect Length Basis:** Independent defects", rendered)
        self.assertIn("**B31G Candidates Assessed:** 1", rendered)
        self.assertIn("**B31G Assessment Length:** 10.0 mm", rendered)
        self.assertIn("**Overall Repair-Zone Span:** 1000.0 mm", rendered)
        self.assertIn(
            "10 mm longitudinal by 10 mm circumferential", rendered,
        )
        self.assertEqual(list(app.exception), [])

    def test_manual_mode_hides_scalar_wall_and_shows_calculated_3t(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        app.number_input(key="wall").set_value(12.0)
        app.selectbox(key="type_").select("Corrosion")
        app.selectbox(key="loc_").select("External").run()
        app.selectbox(key="defect_length_basis").select("Enter manually").run()

        self.assertEqual(
            [field for field in app.number_input if field.key == "rem_"],
            [],
        )
        self.assertIn(
            "3t Interaction Threshold: 36.0 mm",
            [caption.value for caption in app.caption],
        )

    def test_manual_mode_preserves_pairs_and_displays_assessment_table(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app,
            defect_length_basis="Enter manually",
            wall=12.0,
            defect_length=500.0,
        )
        app.session_state["manual_defect_rows"] = [
            {
                "Defect ID": "LONG",
                "Individual longitudinal length [mm]": 300.0,
                "Remaining wall [mm]": 11.0,
                "Separation exceeds 3t": True,
            },
            {
                "Defect ID": "DEEP",
                "Individual longitudinal length [mm]": 10.0,
                "Remaining wall [mm]": 6.0,
                "Separation exceeds 3t": True,
            },
        ]
        app.run()
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()

        rendered = self._rendered_markdown(app)
        self.assertIn("**Defect Length Basis:** Enter manually", rendered)
        self.assertIn("**B31G Candidates Assessed:** 2", rendered)
        self.assertIn("**Governing Defect ID:** LONG", rendered)
        self.assertIn("**B31G Assessment Length:** 300.0 mm", rendered)
        self.assertIn("- **Minimum Remaining Wall:** 6.0 mm", rendered)
        self.assertIn("- **Overall Repair-Zone Span:** 500.0 mm", rendered)
        dataframe_columns = [
            list(element.value.columns) for element in app.dataframe
        ]
        self.assertIn(
            [
                "Defect ID",
                "Individual longitudinal length [mm]",
                "Remaining wall [mm]",
                "Separation exceeds 3t",
            ],
            dataframe_columns,
        )
        self.assertIn(
            [
                "Defect ID",
                "B31G length [mm]",
                "Remaining wall [mm]",
                "Credited pressure [MPa]",
                "Governing",
            ],
            dataframe_columns,
        )
        self.assertEqual(list(app.exception), [])

    def test_new_calculation_clears_manual_governing_defect_output(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app,
            defect_length_basis="Enter manually",
            wall=12.0,
            defect_length=500.0,
        )
        app.session_state["manual_defect_rows"] = [{
            "Defect ID": "D-01",
            "Individual longitudinal length [mm]": 12.0,
            "Remaining wall [mm]": 6.0,
            "Separation exceeds 3t": True,
        }]
        app.run()
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()
        self.assertIn(
            "**Governing Defect ID:** D-01",
            self._rendered_markdown(app),
        )

        next(
            button for button in app.button
            if button.label == "New / Clear Calculation"
        ).click().run()

        self.assertEqual(app.selectbox(key="type_").value, "Select…")
        self.assertEqual(
            app.session_state["defect_length_basis"], "Select…",
        )
        self.assertEqual(app.session_state["manual_defect_rows"], [])
        self.assertFalse(app.session_state["calc_active"])
        self.assertFalse(app.session_state["force_3_layers"])
        self.assertNotIn("Governing Defect ID", self._rendered_markdown(app))
        self.assertEqual(list(app.exception), [])

    def test_invalid_manual_separation_stops_with_actionable_error(self):
        app = AppTest.from_file("PWR110Calculator.py").run()
        self._enter_complete_form_except_cloth_width(
            app,
            defect_length_basis="Enter manually",
            wall=12.0,
            defect_length=500.0,
        )
        app.session_state["manual_defect_rows"] = [{
            "Defect ID": "D-01",
            "Individual longitudinal length [mm]": 10.0,
            "Remaining wall [mm]": 6.0,
            "Separation exceeds 3t": False,
        }]
        app.run()
        app.number_input(key="cloth_width_mm").set_value(300.0).run()

        self._calculate_button(app).click().run()

        self.assertIn(
            "**INPUT ERROR:** Each defect must be confirmed as separated "
            "by more than 3t",
            [error.value for error in app.error],
        )
        self.assertFalse(app.session_state["calc_active"])
        self.assertEqual(list(app.exception), [])

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
