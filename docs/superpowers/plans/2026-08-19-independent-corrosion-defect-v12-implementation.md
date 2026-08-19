# PROWRAP v1.2 Independent Corrosion Defect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated PROWRAP v1.2 calculator with three external-corrosion defect-length modes while retaining one continuous repair and preserving all v1.1 behavior by default.

**Architecture:** Add a focused corrosion-defect domain module that validates mode-specific inputs and produces paired B31G candidates. The existing repair engine evaluates those candidates, selects the lowest credited substrate pressure, and continues to use the overall repair-zone span for ISO repair length and material quantities. Streamlit form state, results, and PDF reporting consume the same result contract.

**Tech Stack:** Python 3, Streamlit, `unittest`, Streamlit `AppTest`, FPDF, pypdf, and the existing pure-Python ASME B31G and ISO 24817 calculation modules.

**Spec:** `docs/superpowers/specs/2026-08-19-independent-corrosion-defect-v12-design.md`

## Global Constraints

- Work only in the isolated `Iso24817Calcv1.2` repository.
- Do not edit, commit, push, deploy, or reconfigure `Iso24817Calcv1.1`.
- Do not edit, commit, push, deploy, or reconfigure the current CalcBatch project.
- Keep v1.2 free of any remote that can push to the v1.1 GitHub repository.
- Default behavior must reproduce v1.1 exactly through `Actual defect length`.
- New modes apply only to external corrosion eligible for B31G substrate credit.
- `3t` means three times nominal wall thickness.
- One continuous repair always covers the complete outer-to-outer repair-zone span.
- `Independent defects` uses a 10 mm longitudinal B31G length and records a 10 mm circumferential-width assumption.
- Manual mode never combines length from one defect with remaining wall from another.
- Invalid or unconfirmed manual inputs stop calculation with an input error.
- No GitHub creation, push, or Streamlit deployment occurs before local v1.2 acceptance.

## File Structure

- Create `corrosion_defects.py`: constants, immutable records, normalization, and mode validation.
- Create `app_identity.py`: v1.2 name, version, and source baseline.
- Modify `prowrap_calculations.py`: candidate evaluation and governing result.
- Modify `calculator_form.py`: conditional blank state and manual-row boundary.
- Modify `PWR110Calculator.py`: UI, calculation wiring, screen results, and PDF.
- Modify `packaging_contract.py`: package the new modules.
- Create focused domain, engine, UI, report, and acceptance tests.
- Create `README_V1.2.md` and a final verification report.

---

### Task 1: v1.2 Identity and Corrosion Defect Domain Contract

**Files:**
- Create: `app_identity.py`
- Create: `corrosion_defects.py`
- Create: `test_corrosion_defects.py`
- Modify: `packaging_contract.py`
- Modify: `test_packaging_contract.py`

**Interfaces:**
- Consumes: pipe dimensions, the selected basis, a single remaining wall, or manual row records.
- Produces: `APP_NAME`, `APP_VERSION`, `SOURCE_BASELINE_REVISION`, mode constants, `IndividualCorrosionDefect`, `CorrosionAssessmentPlan`, `normalize_manual_defects(records)`, and `build_corrosion_assessment_plan(...)`.

- [ ] **Step 1: Write failing identity and domain tests**

```python
import unittest

from app_identity import APP_NAME, APP_VERSION, SOURCE_BASELINE_REVISION
from corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    DEFECT_LENGTH_BASES,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
    build_corrosion_assessment_plan,
    normalize_manual_defects,
)


class CorrosionDefectContractTest(unittest.TestCase):
    def test_v12_identity_and_exact_choices(self):
        self.assertEqual(APP_NAME, "PROWRAP ISO 24817 Calculator v1.2")
        self.assertEqual(APP_VERSION, "1.2")
        self.assertEqual(
            SOURCE_BASELINE_REVISION,
            "7ca0e66ab4f8334fe07fda54b64599f54b1a1256",
        )
        self.assertEqual(DEFECT_LENGTH_BASES, (
            "Actual defect length",
            "Independent defects",
            "Enter manually",
        ))

    def test_actual_plan_pairs_entered_length_and_wall(self):
        plan = build_corrosion_assessment_plan(
            basis=ACTUAL_DEFECT_LENGTH,
            repair_zone_length_mm=1000.0,
            nominal_wall_mm=12.0,
            default_remaining_wall_mm=9.652,
        )
        self.assertEqual(plan.repair_zone_length_mm, 1000.0)
        self.assertEqual(plan.interaction_distance_mm, 36.0)
        self.assertEqual(plan.candidates, (
            IndividualCorrosionDefect("Actual/combined defect", 1000.0, 9.652, True),
        ))

    def test_independent_plan_uses_ten_mm_for_b31g(self):
        plan = build_corrosion_assessment_plan(
            basis=INDEPENDENT_DEFECTS,
            repair_zone_length_mm=1000.0,
            nominal_wall_mm=12.0,
            default_remaining_wall_mm=9.652,
        )
        self.assertEqual(plan.candidates[0].longitudinal_length_mm, 10.0)
        self.assertEqual(plan.minimum_remaining_wall_mm, 9.652)
        self.assertIn("10 mm circumferential", " ".join(plan.assumptions))
        self.assertIn("more than 36 mm", " ".join(plan.assumptions))

    def test_manual_rows_preserve_length_wall_pairs(self):
        defects = normalize_manual_defects([
            {"Defect ID": "LONG", "Individual longitudinal length [mm]": 80,
             "Remaining wall [mm]": 10.5, "Separation exceeds 3t": True},
            {"Defect ID": "DEEP", "Individual longitudinal length [mm]": 12,
             "Remaining wall [mm]": 6.0, "Separation exceeds 3t": True},
        ])
        plan = build_corrosion_assessment_plan(
            basis=ENTER_MANUALLY,
            repair_zone_length_mm=500.0,
            nominal_wall_mm=12.0,
            default_remaining_wall_mm=None,
            manual_defects=defects,
        )
        self.assertEqual(
            [(d.defect_id, d.longitudinal_length_mm, d.remaining_wall_mm)
             for d in plan.candidates],
            [("LONG", 80.0, 10.5), ("DEEP", 12.0, 6.0)],
        )
        self.assertEqual(plan.minimum_remaining_wall_mm, 6.0)
```

- [ ] **Step 2: Add failing validation tests**

```python
    def test_manual_rejects_duplicate_ids_and_unconfirmed_separation(self):
        duplicate = (
            IndividualCorrosionDefect("D-01", 10, 9, True),
            IndividualCorrosionDefect("D-01", 12, 8, True),
        )
        with self.assertRaisesRegex(ValueError, "Defect ID must be unique"):
            build_corrosion_assessment_plan(
                basis=ENTER_MANUALLY, repair_zone_length_mm=100,
                nominal_wall_mm=12, default_remaining_wall_mm=None,
                manual_defects=duplicate,
            )
        with self.assertRaisesRegex(ValueError, "separated by more than 3t"):
            build_corrosion_assessment_plan(
                basis=ENTER_MANUALLY, repair_zone_length_mm=100,
                nominal_wall_mm=12, default_remaining_wall_mm=None,
                manual_defects=(IndividualCorrosionDefect("D-02", 10, 9, False),),
            )

    def test_independent_zone_must_cover_ten_mm_pit(self):
        with self.assertRaisesRegex(ValueError, "at least 10 mm"):
            build_corrosion_assessment_plan(
                basis=INDEPENDENT_DEFECTS, repair_zone_length_mm=9.9,
                nominal_wall_mm=12, default_remaining_wall_mm=9,
            )

    def test_manual_rejects_partial_and_out_of_range_rows(self):
        with self.assertRaisesRegex(ValueError, "remaining wall is required"):
            normalize_manual_defects([{
                "Defect ID": "D-01",
                "Individual longitudinal length [mm]": 10,
                "Remaining wall [mm]": None,
                "Separation exceeds 3t": True,
            }])
        for defect, message in (
            (IndividualCorrosionDefect("ZERO", 0, 9, True), "greater than zero"),
            (IndividualCorrosionDefect("TOO-LONG", 101, 9, True), "cannot exceed"),
            (IndividualCorrosionDefect("TOO-THICK", 10, 12.1, True), "nominal wall"),
        ):
            with self.subTest(defect=defect.defect_id):
                with self.assertRaisesRegex(ValueError, message):
                    build_corrosion_assessment_plan(
                        basis=ENTER_MANUALLY, repair_zone_length_mm=100,
                        nominal_wall_mm=12, default_remaining_wall_mm=None,
                        manual_defects=(defect,),
                    )
```

- [ ] **Step 3: Run the tests and confirm RED**

Run: `python3 -m unittest -v test_corrosion_defects.py`

Expected: FAIL because the new modules do not exist.

- [ ] **Step 4: Implement identity constants**

```python
# app_identity.py
APP_NAME = "PROWRAP ISO 24817 Calculator v1.2"
APP_VERSION = "1.2"
SOURCE_BASELINE_REVISION = "7ca0e66ab4f8334fe07fda54b64599f54b1a1256"
```

- [ ] **Step 5: Implement the immutable domain records and constants**

```python
# corrosion_defects.py
from dataclasses import dataclass
from math import isfinite

ACTUAL_DEFECT_LENGTH = "Actual defect length"
INDEPENDENT_DEFECTS = "Independent defects"
ENTER_MANUALLY = "Enter manually"
DEFECT_LENGTH_BASES = (
    ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS, ENTER_MANUALLY,
)
INDEPENDENT_PIT_LONGITUDINAL_MM = 10.0
INDEPENDENT_PIT_CIRCUMFERENTIAL_MM = 10.0
INTERACTION_DISTANCE_MULTIPLIER = 3.0


@dataclass(frozen=True)
class IndividualCorrosionDefect:
    defect_id: str
    longitudinal_length_mm: float
    remaining_wall_mm: float
    separation_exceeds_3t: bool


@dataclass(frozen=True)
class CorrosionAssessmentPlan:
    basis: str
    repair_zone_length_mm: float
    interaction_distance_mm: float
    candidates: tuple[IndividualCorrosionDefect, ...]
    minimum_remaining_wall_mm: float
    assumptions: tuple[str, ...]
```

Implement a `_finite_number(value, label)` helper that rejects booleans,
nonnumeric values, and nonfinite values with `ValueError`.

- [ ] **Step 6: Implement manual normalization and plan validation**

`normalize_manual_defects(records)` shall ignore completely blank rows, reject
partial rows, strip IDs, convert numbers, and return a tuple of
`IndividualCorrosionDefect`.

`build_corrosion_assessment_plan` shall:

```python
def build_corrosion_assessment_plan(
    *, basis, repair_zone_length_mm, nominal_wall_mm,
    default_remaining_wall_mm, manual_defects=(),
):
    # Validate the exact basis and positive zone/nominal wall.
    # Actual: one paired candidate using zone and default wall.
    # Independent: one paired 10 mm candidate using default wall.
    # Manual: use the supplied paired candidates.
    # Reject blank/duplicate IDs, lengths outside (0, zone], walls outside
    # [0, nominal], and any false separation confirmation.
    # Return minimum wall, 3*nominal, and permanent assumptions.
```

Use these exact independent assumptions:

```python
(
    "Each corrosion defect is 10 mm longitudinal by 10 mm circumferential.",
    f"Each corrosion defect is separated from every other defect by more than {3 * nominal:g} mm (3t).",
    "Each corrosion defect uses the entered remaining wall.",
)
```

- [ ] **Step 7: Add both modules to desktop packaging**

Add `app_identity.py` and `corrosion_defects.py` to `CALCULATOR_MODULES`; assert
both names in `test_packaging_contract.py`.

- [ ] **Step 8: Run focused tests and confirm GREEN**

Run: `python3 -m unittest -v test_corrosion_defects.py test_packaging_contract.py`

Expected: all tests PASS.

- [ ] **Step 9: Commit Task 1**

```bash
git add app_identity.py corrosion_defects.py test_corrosion_defects.py packaging_contract.py test_packaging_contract.py
git commit -m "feat: define v1.2 corrosion defect modes"
```

---

### Task 2: Candidate-Based B31G Engine Integration

**Files:**
- Create: `test_corrosion_defect_modes.py`
- Modify: `prowrap_calculations.py`
- Modify: `test_current_calculation_baseline.py`
- Modify: `test_typea_class3_adapter.py`

**Interfaces:**
- Consumes: `IndividualCorrosionDefect`, `build_corrosion_assessment_plan`, and existing `assess_b31g`.
- Produces: `calculate_repair(..., defect_length_basis=ACTUAL_DEFECT_LENGTH, individual_defects=())` and the new traceability result keys specified below.

- [ ] **Step 1: Write failing default and independent engine tests**

```python
import unittest

from b31g import assess_b31g
from corrosion_defects import INDEPENDENT_DEFECTS
from prowrap_calculations import calculate_repair
from test_current_calculation_baseline import default_inputs


class CorrosionDefectModesTest(unittest.TestCase):
    def test_default_mode_keeps_exact_v11_baseline(self):
        result = calculate_repair(**default_inputs())
        self.assertEqual(result["defect_length_basis"], "Actual defect length")
        self.assertAlmostEqual(result["p_steel_capacity"], 9.951873620726573)
        self.assertAlmostEqual(result["iso_length"], 388.933816016055)

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
```

- [ ] **Step 2: Write failing manual pairing and governing tests**

```python
from corrosion_defects import ENTER_MANUALLY, IndividualCorrosionDefect

    def test_manual_mode_preserves_pairs_and_selects_lowest_credit(self):
        result = calculate_repair(
            **default_inputs(length=500.0, rem_wall=6.0),
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("LONG", 300.0, 11.0, True),
                IndividualCorrosionDefect("DEEP", 10.0, 6.0, True),
            ),
        )
        items = {item["defect_id"]: item for item in result["b31g_assessments"]}
        self.assertEqual((items["LONG"]["length_mm"], items["LONG"]["remaining_wall_mm"]), (300.0, 11.0))
        self.assertEqual((items["DEEP"]["length_mm"], items["DEEP"]["remaining_wall_mm"]), (10.0, 6.0))
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
```

- [ ] **Step 3: Run focused engine tests and confirm RED**

Run: `python3 -m unittest -v test_corrosion_defect_modes.py`

Expected: FAIL because `calculate_repair` lacks the new arguments and results.

- [ ] **Step 4: Extend `calculate_repair` without breaking callers**

Add keyword defaults after `cloth_width_mm`:

```python
defect_length_basis=ACTUAL_DEFECT_LENGTH,
individual_defects=(),
```

After mechanism/location normalization, construct a plan only for external
corrosion. Use its minimum remaining wall for wall-loss, severe-loss routing,
and supporting checks. Ignore the selector for every other route.

- [ ] **Step 5: Evaluate every paired B31G candidate**

For each external-corrosion candidate, call existing `assess_b31g` with that
candidate's paired length and remaining wall even when severe loss will force
the structural route to Type B. Store:

```python
{
    "defect_id": defect.defect_id,
    "length_mm": defect.longitudinal_length_mm,
    "remaining_wall_mm": defect.remaining_wall_mm,
    "credited_pressure_mpa": assessment["p_s_mpa"] if assessment["applicable"] else 0.0,
    "assessment": assessment,
}
```

Choose the first minimum credited pressure in input order. Feed that pressure
into the existing ISO laminate calculation. Retain `length` as the overall
repair-zone span in Formula 20 and material calculations.

When any candidate drives minimum remaining wall below 1 mm, keep the existing
Type B routing and zero substrate credit while retaining the candidate
assessment and governing ID for traceability.

- [ ] **Step 6: Return exact traceability fields**

Add:

```python
"defect_length_basis": applied_basis,
"repair_zone_length_mm": length,
"interaction_distance_mm": 3.0 * wall,
"defect_basis_assumptions": assumptions,
"b31g_assessments": tuple(b31g_assessments),
"governing_defect_id": governing_id,
"governing_b31g_length_mm": governing_length,
"governing_b31g_remaining_wall_mm": governing_wall,
```

Keep `b31g_details` as the governing assessment so existing consumers remain
compatible. Prefix candidate-specific warnings with Defect ID and de-duplicate
identical global warnings.

- [ ] **Step 7: Verify optional Type A/Class 3 inputs**

Add a regression in `test_typea_class3_adapter.py` proving that the optional
check receives `result["rem_wall_eol"]` and the governing substrate credit,
not a non-governing manual defect.

- [ ] **Step 8: Run engine and inherited regressions**

Run:

```bash
python3 -m unittest -v test_corrosion_defect_modes.py test_current_calculation_baseline.py test_input_validation.py test_b31g.py test_typea_class3_adapter.py test_typea_baseline_matches_rigorous.py
```

Expected: all tests PASS, including exact inherited numerical baselines.

- [ ] **Step 9: Commit Task 2**

```bash
git add prowrap_calculations.py test_corrosion_defect_modes.py test_current_calculation_baseline.py test_typea_class3_adapter.py
git commit -m "feat: assess independent corrosion defects in v1.2"
```

---

### Task 3: Conditional Form State and Manual Row Boundary

**Files:**
- Modify: `calculator_form.py`
- Modify: `test_calculator_form.py`

**Interfaces:**
- Consumes: exact mode constants and `normalize_manual_defects`.
- Produces: state keys `defect_length_basis`, `manual_defect_rows`, conditional `missing_required_fields(values)`, and `manual_defects_from_state(values)`.

- [ ] **Step 1: Extract a complete-state test helper and write failing conditional tests**

```python
from corrosion_defects import ACTUAL_DEFECT_LENGTH, ENTER_MANUALLY

def complete_values():
    values = dict(INPUT_DEFAULTS)
    values.update({
        "customer": "PROTAP", "location": "Turkey", "report_no": "V12-001",
        "od": 457.2, "wall": 9.53, "yield_str": 359.0,
        "pres": 50.0, "temp": 40.0, "type_": "Corrosion",
        "loc_": "External", "len_": 100.0, "rem_": 4.5,
        "design_life": 20, "df": 0.72, "installation_temp": 20.0,
        "component_type": "Straight", "cyclic_derating_factor": 1.0,
        "axial_load_case": 0, "cloth_width_mm": 300.0,
        "defect_length_basis": ACTUAL_DEFECT_LENGTH,
    })
    return values

class CalculatorFormTest(unittest.TestCase):
    def test_external_corrosion_requires_length_basis(self):
        values = complete_values()
        values["defect_length_basis"] = "Select…"
        self.assertIn("Defect Length Basis", missing_required_fields(values))

    def test_manual_mode_uses_table_instead_of_single_remaining_wall(self):
        values = complete_values()
        values.update({
            "defect_length_basis": ENTER_MANUALLY,
            "rem_": None,
            "manual_defect_rows": [{
                "Defect ID": "D-01",
                "Individual longitudinal length [mm]": 10.0,
                "Remaining wall [mm]": 8.0,
                "Separation exceeds 3t": True,
            }],
        })
        self.assertEqual(missing_required_fields(values), [])

    def test_dent_does_not_require_corrosion_basis(self):
        values = complete_values()
        values.update({"type_": "Dent no-crack", "defect_length_basis": "Select…"})
        self.assertNotIn("Defect Length Basis", missing_required_fields(values))
```

- [ ] **Step 2: Write a failing reset test for mutable table state**

```python
    def test_new_calculation_clears_new_mode_and_rows(self):
        state = complete_values()
        state.update({
            "manual_defect_rows": [{"Defect ID": "D-01"}],
            "calc_active": True,
            "force_3_layers": True,
        })
        new_calculation(state)
        self.assertEqual(state["defect_length_basis"], "Select…")
        self.assertEqual(state["manual_defect_rows"], [])
        self.assertFalse(state["calc_active"])
        self.assertFalse(state["force_3_layers"])
```

- [ ] **Step 3: Run form tests and confirm RED**

Run: `python3 -m unittest -v test_calculator_form.py`

Expected: FAIL because the new state and conditional requirements are absent.

- [ ] **Step 4: Add safe defaults and deep-copy resets**

Add these defaults:

```python
"defect_length_basis": NEUTRAL_CHOICE,
"manual_defect_rows": [],
```

Use `copy.deepcopy(value)` in `initialise_inputs` and `new_calculation` so
mutable table rows are never shared across sessions.

- [ ] **Step 5: Implement conditional completeness and state normalization**

External corrosion requires `Defect Length Basis`. Manual mode does not require
the single `rem_` field; instead it requires at least one normalized manual
record. All other routes retain their existing required fields.

```python
def manual_defects_from_state(values):
    records = values.get("manual_defect_rows") or []
    if hasattr(records, "to_dict"):
        records = records.to_dict("records")
    return normalize_manual_defects(records)
```

Return `Individual defects table` as the missing label when manual mode has no
complete rows. Detailed row errors remain `ValueError` messages presented by
the calculation boundary.

- [ ] **Step 6: Run focused tests and confirm GREEN**

Run: `python3 -m unittest -v test_calculator_form.py`

Expected: all tests PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add calculator_form.py test_calculator_form.py
git commit -m "feat: add v1.2 corrosion mode form state"
```

---

### Task 4: Streamlit Inputs, Calculation Wiring, and Engineering Results

**Files:**
- Modify: `PWR110Calculator.py`
- Modify: `test_streamlit_form_submission.py`

**Interfaces:**
- Consumes: v1.2 identity, the domain constants, `manual_defects_from_state`, and Task 2 result keys.
- Produces: the conditional selector, dynamic manual table, exact engine arguments, and visible governing-defect traceability.

- [ ] **Step 1: Write failing selector visibility tests**

```python
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
```

- [ ] **Step 2: Write a failing independent-mode AppTest**

Extend the complete-form helper with a `defect_length_basis` argument. Enter
the 1016 mm, 1000 mm overall-span example and assert:

```python
rendered = self._rendered_markdown(app)
self.assertIn("**Defect Length Basis:** Independent defects", rendered)
self.assertIn("**B31G Assessment Length:** 10.0 mm", rendered)
self.assertIn("**Overall Repair-Zone Span:** 1000.0 mm", rendered)
self.assertIn("10 mm longitudinal by 10 mm circumferential", rendered)
self.assertEqual(list(app.exception), [])
```

- [ ] **Step 3: Run AppTest and confirm RED**

Run: `python3 -m unittest -v test_streamlit_form_submission.py`

Expected: FAIL because the selector and traceability are absent.

- [ ] **Step 4: Add v1.2 branding and the selector immediately after length**

Use `APP_NAME` for the title and include `v1.2` in page metadata. Render the
selector only when mechanism is Corrosion and location is External:

```python
is_external_corrosion = type_ == "Corrosion" and loc_ == "External"
defect_length_basis = ACTUAL_DEFECT_LENGTH
manual_defects = ()
if is_external_corrosion:
    defect_length_basis = st.sidebar.selectbox(
        "Defect Length Basis",
        [NEUTRAL_CHOICE, *DEFECT_LENGTH_BASES],
        key="defect_length_basis",
        on_change=reset_calc,
    )
```

- [ ] **Step 5: Render mode-specific inputs**

For `Actual defect length`, show the existing remaining-wall input.

For `Independent defects`, show the existing remaining-wall input plus the
three permanent assumptions and calculated `3t` threshold.

For `Enter manually`, hide the single remaining-wall input and use a dynamic
`st.data_editor` with exact columns:

```python
column_config={
    "Defect ID": st.column_config.TextColumn(required=True),
    "Individual longitudinal length [mm]": st.column_config.NumberColumn(
        min_value=0.01, required=True,
    ),
    "Remaining wall [mm]": st.column_config.NumberColumn(
        min_value=0.0, required=True,
    ),
    "Separation exceeds 3t": st.column_config.CheckboxColumn(required=True),
}
```

Persist returned records in `manual_defect_rows`, normalize them, and derive
`rem_` as their minimum remaining wall for the unchanged positional engine
argument.

- [ ] **Step 6: Wire mode and defects through `run_calculation`**

Add `defect_length_basis` and `individual_defects` to `run_calculation`, then
pass them by keyword to `calculate_repair`. Nonexternal routes pass actual mode
and an empty tuple.

- [ ] **Step 7: Render governing-defect traceability**

Show:

```python
st.write(f"**Defect Length Basis:** {report_data['defect_length_basis']}")
st.write(f"**Overall Repair-Zone Span:** {report_data['repair_zone_length_mm']:.1f} mm")
st.write(f"**3t Interaction Threshold:** {report_data['interaction_distance_mm']:.1f} mm")
st.write(f"**Governing Defect ID:** {report_data['governing_defect_id']}")
st.write(f"**B31G Assessment Length:** {report_data['governing_b31g_length_mm']:.1f} mm")
st.write(f"**B31G Assessment Remaining Wall:** {report_data['governing_b31g_remaining_wall_mm']:.3f} mm")
```

Render assumptions as information notes. Manual mode shows a compact dataframe
of all stored B31G assessments without recalculating them in the UI.

- [ ] **Step 8: Correct the method-statement labels**

Use the result model's minimum remaining wall and overall repair-zone span.
Show governing Defect ID for external corrosion. Keep dent wording unchanged.

- [ ] **Step 9: Run focused UI regressions**

Run:

```bash
python3 -m unittest -v test_streamlit_form_submission.py test_calculator_form.py test_corrosion_defect_modes.py test_dent_mechanism_split.py
```

Expected: all tests PASS with no Streamlit exceptions.

- [ ] **Step 10: Commit Task 4**

```bash
git add PWR110Calculator.py test_streamlit_form_submission.py
git commit -m "feat: expose corrosion defect modes in v1.2"
```

---

### Task 5: PDF Traceability and Reset-Safe Reporting

**Files:**
- Modify: `PWR110Calculator.py`
- Modify: `test_report_wording.py`
- Modify: `test_calculator_form.py`

**Interfaces:**
- Consumes: Task 2 result fields.
- Produces: v1.2-branded PDF reports with permanent assumptions and manual candidate details.

- [ ] **Step 1: Extract a PDF-text helper and write failing independent report test**

```python
def pdf_text(pdf_bytes):
    return "\n".join(
        page.extract_text() or ""
        for page in PdfReader(BytesIO(pdf_bytes)).pages
    )

def test_independent_pdf_records_assumptions_and_two_lengths(self):
    report = calculate_repair(
        **default_inputs(length=1000.0, rem_wall=9.0),
        defect_length_basis=INDEPENDENT_DEFECTS,
    )
    text = pdf_text(create_pdf(report))
    self.assertIn("PROWRAP COMPOSITE REPAIR REPORT - v1.2", text)
    self.assertIn("Defect Length Basis: Independent defects", text)
    self.assertIn("Overall Repair-Zone Span: 1000.0 mm", text)
    self.assertIn("B31G Assessment Length: 10.0 mm", text)
    self.assertIn("10 mm longitudinal by 10 mm circumferential", text)
```

- [ ] **Step 2: Write failing manual report test**

```python
def test_manual_pdf_lists_candidates_and_governing_defect(self):
    report = calculate_repair(
        **default_inputs(length=500.0, rem_wall=6.0),
        defect_length_basis=ENTER_MANUALLY,
        individual_defects=(
            IndividualCorrosionDefect("D-01", 80.0, 10.5, True),
            IndividualCorrosionDefect("D-02", 12.0, 6.0, True),
        ),
    )
    text = pdf_text(create_pdf(report))
    self.assertIn("Defect Length Basis: Enter manually", text)
    self.assertIn("D-01", text)
    self.assertIn("D-02", text)
    self.assertIn(f"Governing Defect: {report['governing_defect_id']}", text)
```

- [ ] **Step 3: Run report tests and confirm RED**

Run: `python3 -m unittest -v test_report_wording.py`

Expected: FAIL because v1.2 fields are absent.

- [ ] **Step 4: Extend `create_pdf` from stored result data**

Use `APP_VERSION` in the title. Add basis, overall span, `3t`, governing ID,
governing paired dimensions, and assumptions to Defect Assessment. In manual
mode add one compact line per item in `b31g_assessments`; do not call B31G from
the report generator.

Check available page space before the candidate list and installation
checklist so each section remains legible.

- [ ] **Step 5: Assert complete reset and no stale report state**

Expand `test_calculator_form.py` to confirm new calculation clears mode, manual
rows, calculation activation, and force-three-layers state. Add an AppTest that
calculates manual mode, clears the form, and confirms governing-defect output is
gone.

- [ ] **Step 6: Run report, reset, and dent regressions**

Run:

```bash
python3 -m unittest -v test_report_wording.py test_calculator_form.py test_streamlit_form_submission.py
```

Expected: all tests PASS; dent reports still contain no B31G wording.

- [ ] **Step 7: Commit Task 5**

```bash
git add PWR110Calculator.py test_report_wording.py test_calculator_form.py test_streamlit_form_submission.py
git commit -m "feat: report v1.2 governing corrosion defect"
```

---

### Task 6: Side-by-Side Acceptance and Operator Documentation

**Files:**
- Create: `test_v12_acceptance.py`
- Create: `README_V1.2.md`
- Modify: `DESKTOP_BUILD.md`
- Modify: `EMPLOYEE_MAC_INSTALL.md`

**Interfaces:**
- Consumes: completed v1.2 engine, UI identity, and report contract.
- Produces: executable numerical acceptance evidence and operator/release guidance.

- [ ] **Step 1: Write the side-by-side acceptance test**

```python
import unittest

from corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    ENTER_MANUALLY,
    INDEPENDENT_DEFECTS,
    IndividualCorrosionDefect,
)
from prowrap_calculations import calculate_repair


class V12AcceptanceTest(unittest.TestCase):
    def test_same_zone_uses_mode_specific_b31g_and_continuous_coverage(self):
        base = dict(
            customer="PROTAP", location="Turkey", report_no="V12-ACC",
            od=1016.0, wall=12.0, pressure=104.9, temp=40.0,
            defect_type="Corrosion", defect_loc="External", length=1000.0,
            rem_wall=9.652, yield_strength=450.0, design_factor=0.72,
            design_life=20, cloth_width_mm=500.0,
        )
        actual = calculate_repair(
            **base, defect_length_basis=ACTUAL_DEFECT_LENGTH,
        )
        independent = calculate_repair(
            **base, defect_length_basis=INDEPENDENT_DEFECTS,
        )
        manual = calculate_repair(
            **base,
            defect_length_basis=ENTER_MANUALLY,
            individual_defects=(
                IndividualCorrosionDefect("D-01", 10.0, 9.652, True),
                IndividualCorrosionDefect("D-02", 35.0, 10.0, True),
            ),
        )

        self.assertAlmostEqual(actual["p_steel_capacity"], 7.571542406120033)
        self.assertAlmostEqual(independent["p_steel_capacity"], 8.82257484144555)
        self.assertGreater(actual["num_plies"], independent["num_plies"])
        self.assertEqual(independent["governing_b31g_length_mm"], 10.0)
        self.assertIn(manual["governing_defect_id"], {"D-01", "D-02"})
        for result in (actual, independent, manual):
            covered_zone = (
                result["iso_length"]
                - 2.0 * result["overlap_length"]
                - 2.0 * result["taper_length"]
            )
            self.assertAlmostEqual(covered_zone, 1000.0)
```

- [ ] **Step 2: Run acceptance and investigate mismatches before changing expectations**

Run: `python3 -m unittest -v test_v12_acceptance.py`

Expected: PASS. For a mismatch, trace candidate pressure, governing selection,
ISO pressure deficit, overlap, and taper before changing an expected value.

- [ ] **Step 3: Write `README_V1.2.md`**

Document:

- all three exact choices and their appropriate use;
- nominal-wall meaning of `t` and the `3t` independence threshold;
- independent mode's 10 x 10 mm assumptions;
- manual table columns and confirmation;
- B31G length versus overall repair-zone span;
- continuous coverage of the complete outer-to-outer span;
- preliminary-screening and competent-engineering-review limitations;
- local setup, run, and test commands;
- the prohibition on overwriting or redeploying v1.1 and current CalcBatch.

- [ ] **Step 4: Update desktop documents only for v1.2 identity and paths**

Update `DESKTOP_BUILD.md` and `EMPLOYEE_MAC_INSTALL.md` from v1.1 to v1.2
product/repository wording. Preserve the current arm64, M4/M5, packaging, and
verification requirements.

- [ ] **Step 5: Run the complete inherited and new suite**

Run: `python3 -m unittest discover -v`

Expected: every test PASS, except only pre-existing environment-guarded tests
whose required platform components are unavailable.

- [ ] **Step 6: Verify source isolation**

Run:

```bash
git diff --check
git remote -v
git status --short
git -C /Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split status --short
git -C /Users/can/Documents/Codex/2026-08-14/i/outputs/Iso24817CalcBatch/.worktrees/feature-batch-calculator diff --stat
```

Expected:

- v1.2 has no push remote and only intended Task 6 files are pending;
- v1.1 prints no status entries;
- current CalcBatch has no tracked-code diff from this work;
- its pre-existing untracked `outputs/` remains preserved and uncommitted.

- [ ] **Step 7: Commit Task 6**

```bash
git add test_v12_acceptance.py README_V1.2.md DESKTOP_BUILD.md EMPLOYEE_MAC_INSTALL.md
git commit -m "docs: complete v1.2 corrosion mode acceptance"
```

---

### Task 7: Final Verification and CalcBatch-v1.2 Handoff

**Files:**
- Create: `docs/superpowers/reports/2026-08-19-v12-independent-corrosion-verification.md`
- Modify only after a reproduced v1.2 defect: the responsible Task 1-6 file and its regression test.

**Interfaces:**
- Consumes: all committed v1.2 behavior and tests.
- Produces: a reproducible local-release verdict and the bounded next phase for a separate CalcBatch-v1.2.

- [ ] **Step 1: Run a fresh complete suite**

Run: `python3 -m unittest discover -v`

Record exact pass, fail, error, and skip totals in the verification report.

- [ ] **Step 2: Run focused engineering acceptance**

Run:

```bash
python3 -m unittest -v test_v12_acceptance.py test_corrosion_defect_modes.py test_b31g.py test_typea_class3_adapter.py test_report_wording.py test_streamlit_form_submission.py
```

Record exact results and the 1016 mm example's actual-versus-independent safe
substrate pressures and installed plies.

- [ ] **Step 3: Verify blank opening and every UI route**

Use Streamlit `AppTest` in a fresh process to verify:

- blank v1.2 opens without calculation output;
- actual mode reproduces inherited behavior;
- independent mode shows 10 mm for B31G and 1000 mm for coverage;
- manual mode lists candidates and governing defect;
- reset removes mode, table rows, and stale results;
- dent routes neither show nor consume the corrosion selector.

- [ ] **Step 4: Verify all three PDF routes**

Generate actual, independent, and manual reports with `create_pdf`. Parse each
with pypdf and record that it contains v1.2 identity, mode, overall span,
governing defect information, and applicable permanent assumptions.

- [ ] **Step 5: Verify repository isolation**

Record:

- v1.2 HEAD and clean status;
- no v1.2 remote points to `Iso24817Calcv1.1`;
- v1.1 remains at
  `7ca0e66ab4f8334fe07fda54b64599f54b1a1256` with a clean worktree;
- current CalcBatch tracked files remain unchanged.

- [ ] **Step 6: Write the verification report**

Include commands, results, numerical acceptance values, remaining limitations,
and this exact boundary statement:

```text
CalcBatch-v1.2 has not been created or modified in this phase. After the user
accepts the verified v1.2 calculator, create a separate CalcBatch-v1.2
repository and write a batch-specific specification using the verified v1.2
engine contract. Never modify or redeploy the current CalcBatch application.
```

- [ ] **Step 7: Commit the verification report**

```bash
git add docs/superpowers/reports/2026-08-19-v12-independent-corrosion-verification.md
git commit -m "test: verify isolated v1.2 corrosion modes"
```

- [ ] **Step 8: Run the final clean-state check**

Run:

```bash
git status --short
git log --oneline --decorate -8
git show --check --stat HEAD
```

Expected: clean v1.2 worktree, documented commits, and no whitespace errors.
Do not create a remote, push, or deploy in this task.
