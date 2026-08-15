from io import BytesIO
import unittest

from pypdf import PdfReader

from PWR110Calculator import create_pdf
from prowrap_calculations import calculate_repair
from test_current_calculation_baseline import default_inputs


class ReportWordingTest(unittest.TestCase):
    @staticmethod
    def _dent_report_pages(mechanism):
        report_data = calculate_repair(**default_inputs(
            defect_type=mechanism,
            rem_wall=9.53,
        ))

        pdf_bytes = create_pdf(report_data)

        assert pdf_bytes.startswith(b"%PDF")
        reader = PdfReader(BytesIO(pdf_bytes))
        return [page.extract_text() or "" for page in reader.pages]

    @classmethod
    def _dent_report_text(cls, mechanism):
        return "\n".join(cls._dent_report_pages(mechanism))

    def test_dent_pdf_keeps_installation_checklist_together(self):
        for mechanism in ("Dent w/crack", "Dent no-crack"):
            with self.subTest(mechanism=mechanism):
                pages = self._dent_report_pages(mechanism)
                self.assertTrue(any(
                    "5. Installation Checklist (Method Statement)" in page
                    and "5. Quality Control:" in page
                    for page in pages
                ))

    def test_dent_with_crack_pdf_reports_full_pressure_laminate_basis(self):
        text = self._dent_report_text("Dent w/crack")

        self.assertIn("Dent w/crack - full-pressure laminate", text)
        self.assertIn("Substrate Allowable Pressure p_s: 0.00 MPa (0.00 bar)", text)
        self.assertIn("Composite Pressure Deficit: 5.00 MPa", text)
        self.assertNotIn("B31G", text)
        self.assertIn(
            "Preliminary basis: selected ISO 24817 / ASME PCC-2 concepts",
            text,
        )

    def test_dent_no_crack_pdf_reports_substrate_load_sharing_basis(self):
        text = self._dent_report_text("Dent no-crack")

        self.assertIn("Dent no-crack - substrate load sharing", text)
        self.assertIn("Allowable Pipe Stress S_allow: 258.48 MPa", text)
        self.assertIn("Substrate Allowable Pressure p_s: 10.78 MPa (107.76 bar)", text)
        self.assertIn("Composite Pressure Deficit: 0.00 MPa", text)
        self.assertNotIn("B31G", text)
        self.assertIn(
            "Preliminary basis: selected ISO 24817 / ASME PCC-2 concepts",
            text,
        )

    def test_internal_dent_no_crack_pdf_reports_type_b_basis(self):
        report_data = calculate_repair(**default_inputs(
            defect_type="Dent no-crack",
            defect_loc="Internal",
            rem_wall=9.53,
        ))

        pdf_bytes = create_pdf(report_data)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        text = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(BytesIO(pdf_bytes)).pages
        )
        self.assertIn("Repair Logic: Type B (Total Replacement)", text)
        self.assertIn("Calculation Basis: Type B full replacement", text)
        self.assertNotIn("substrate load sharing", text)


if __name__ == "__main__":
    unittest.main()
