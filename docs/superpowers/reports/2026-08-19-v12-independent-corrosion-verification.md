# PROWRAP v1.2 Independent Corrosion Verification

**Date:** 2026-08-19
**Repository:** isolated `Iso24817Calcv1.2` worktree
**Pre-report HEAD:** `ea2fb0d36469c95ce2f18332d89b7f6eee0c6206`
**Verdict:** The isolated v1.2 source release passes the fresh complete suite,
the focused engineering acceptance suite, independent Streamlit route checks,
and parsed-PDF traceability checks. It is ready for user review as a local
source release. No remote, push, deployment, or batch-project creation was
performed.

## Fresh automated verification

### Complete suite

Command:

```bash
python3 -m unittest discover -v
```

Result: `Ran 140 tests in 1.573s` and `OK`.

| Passed | Failures | Errors | Skipped |
| ---: | ---: | ---: | ---: |
| 140 | 0 | 0 | 0 |

The recurring Streamlit bare-mode `missing ScriptRunContext` messages were
warnings only; the process exited 0.

### Focused engineering acceptance

Command:

```bash
python3 -m unittest -v test_v12_acceptance.py test_corrosion_defect_modes.py test_b31g.py test_typea_class3_adapter.py test_report_wording.py test_streamlit_form_submission.py
```

Result: `Ran 40 tests in 1.237s` and `OK`.

| Passed | Failures | Errors | Skipped |
| ---: | ---: | ---: | ---: |
| 40 | 0 | 0 | 0 |

A supplemental focused check of the desktop bundle contract and v1.2 identity
ran 2 tests and passed 2, with 0 failures, 0 errors, and 0 skips. It verifies
that the configured physical desktop filename remains
`PROWRAP ISO 24817 Calculator.app` and the bundle version metadata remains
`1.2`. No distributable bundle was built, signed, notarized, or deployed in
this verification phase.

## 1016 mm numerical acceptance

Inputs common to the comparison were OD 1016 mm, nominal wall 12 mm, design
pressure 104.9 bar, remaining wall 9.652 mm, yield strength 450 MPa, design
factor 0.72, design life 20 years, overall repair-zone span 1000 mm, and 500 mm
cloth width.

| Route | B31G length | Safe substrate pressure | Installed plies | Continuous covered zone before overlap/taper |
| --- | ---: | ---: | ---: | ---: |
| Actual defect length | 1000 mm | 7.571542406120033 MPa (75.71542406120033 bar) | 12 | 1000 mm |
| Independent defects | 10 mm | 8.82257484144555 MPa (88.2257484144555 bar) | 7 | 1000 mm |
| Manual, governing D-02 | 35 mm | 8.783461911867068 MPa (87.83461911867068 bar) | 7 | 1000 mm |

The Actual route retained the inherited full-length B31G behavior. The
Independent route used the permanent 10 mm longitudinal by 10 mm
circumferential pit assumption for B31G while preserving the full 1000 mm
repair-zone coverage. The manual route preserved the entered pairs D-01
(10 mm, 9.652 mm) and D-02 (35 mm, 10.0 mm) and selected D-02 as governing.

## Fresh Streamlit route verification

A separate Python process used Streamlit `AppTest` against
`PWR110Calculator.py` and verified:

- a blank v1.2 opening displayed the v1.2 identity, no metrics, no success
  output, no PDF download, and `calc_active=False`;
- Actual defect length displayed one candidate, a 1000 mm B31G length, a
  1000 mm overall span, `Actual/combined defect` as governing, and 12 plies;
- Independent defects displayed one candidate, a 10 mm B31G length, the 10 x
  10 mm pit assumption, a 1000 mm overall span, and 7 plies;
- Enter manually displayed both candidate tables, retained both pairs,
  displayed D-02 as governing with a 35 mm B31G length, and returned 7 plies;
- New / Clear Calculation restored the neutral mechanism and basis, emptied
  manual rows, set `calc_active=False`, removed metrics, and removed stale
  governing-defect output;
- both `Dent w/crack` and `Dent no-crack` hid the corrosion selector and
  calculated without consuming it, including when an unreachable unknown
  selector value was injected directly into session state.

Expected structural-compliance notices are rendered by the application using
Streamlit error styling. They were distinguished from input-validation errors
when evaluating the route results.

## Parsed-PDF route verification

Fresh Actual, Independent, and Manual reports were generated with
`create_pdf`, parsed with `pypdf`, and checked field-by-field. Each was a
valid, two-page PDF with v1.2 identity and zero missing asserted fields.

| Route | Asserted fields | Confirmed traceability |
| --- | ---: | --- |
| Actual | 16 | identity, mode, 1000 mm span, candidate count, governing ID, B31G length and remaining wall, credited pressure, installed design fields, continuous/interacting-feature assumption |
| Independent | 18 | all common fields plus the 10 x 10 mm pit, greater-than-36 mm (3t) separation, and entered-remaining-wall assumptions |
| Manual | 19 | all common fields plus D-01 and D-02 candidate lines, governing D-02, and greater-than-36 mm (3t) separation assumption |

This explicit parsed-PDF check closes the earlier test-coverage concern that
the unit tests did not directly assert every new traceability field. No PDF
route defect was reproduced.

## Repository isolation

- The isolated v1.2 worktree was clean before this report at
  `ea2fb0d36469c95ce2f18332d89b7f6eee0c6206`.
- `git remote -v` returned no v1.2 remotes; therefore no v1.2 remote points to
  `Iso24817Calcv1.1` and no push route was created.
- The protected v1.1 worktree at
  `/Users/can/Documents/Codex/2026-08-14/i/work/Iso24817Calcv11-dent-split`
  is clean at the required
  `7ca0e66ab4f8334fe07fda54b64599f54b1a1256`.
- The current CalcBatch worktree at
  `/Users/can/Documents/Codex/2026-08-14/i/outputs/Iso24817CalcBatch/.worktrees/feature-batch-calculator`
  has no tracked or staged diff. Its pre-existing untracked `outputs/`
  directory remains preserved and uncommitted.
- No v1.1 or current CalcBatch file, repository configuration, application,
  or deployment was changed.

## Remaining limitations and engineering boundary

- `missing_required_fields` treats an arbitrary unknown non-neutral external-
  corrosion basis as present. A direct-state reproduction returned no missing
  field at that form-precheck layer, after which the engine correctly rejected
  it with `Defect length basis must be one of the exact supported choices`.
  This is not operator-reachable through the UI, whose selector exposes only
  the three exact supported values, and it did not affect dent routing. It is
  recorded as a non-load-bearing defense-in-depth limitation; no production
  code was changed.
- Independent and manual separation remain engineering assertions, not
  geometry automatically inferred by the calculator. Competent engineering
  review must confirm the greater-than-3t separation and the applicability of
  the 10 x 10 mm independent-pit model before issue.
- The result is local source verification. It is not evidence of signing,
  notarization, installation on another Mac, publication, or deployment.

CalcBatch-v1.2 has not been created or modified in this phase. After the user
accepts the verified v1.2 calculator, create a separate CalcBatch-v1.2
repository and write a batch-specific specification using the verified v1.2
engine contract. Never modify or redeploy the current CalcBatch application.

## Review fix round 1: reproducible route evidence

The following three commands were rerun from the isolated v1.2 repository at
the Task 7 review-fix HEAD. Each command is self-contained, exits nonzero on
an assertion failure, and prints a machine-readable result only after all of
its assertions pass.

### Fresh-process UI verifier

Command:

```bash
python3 - 2>/dev/null <<'PY'
import json
from streamlit.testing.v1 import AppTest
from calculator_form import missing_required_fields
from prowrap_calculations import calculate_repair


def text(app):
    return "\n".join([e.value for e in app.markdown] + [e.value for e in app.info])


def calculate_button(app):
    return next(button for button in app.button if button.label == "Calculate & Optimize")


def input_errors(app):
    return [e.value for e in app.error if "INPUT ERROR" in e.value]


def fill(app, mechanism="Corrosion", basis=None):
    for key, value in {"customer": "PROTAP", "location": "Turkey", "report_no": "V12-UI"}.items():
        app.text_input(key=key).set_value(value)
    for key, value in {
        "od": 1016.0, "wall": 12.0, "yield_str": 450.0,
        "pres": 104.9, "temp": 40.0, "len_": 1000.0,
        "rem_": 9.652, "design_life": 20, "df": 0.72,
        "installation_temp": 20.0, "cyclic_derating_factor": 1.0,
    }.items():
        fields = [field for field in app.number_input if field.key == key]
        if fields:
            fields[0].set_value(value)
    app.selectbox(key="type_").select(mechanism)
    app.selectbox(key="loc_").select("External")
    app.selectbox(key="component_type").select("Straight")
    app.selectbox(key="axial_load_case").select(0)
    app.run()
    if basis is not None:
        app.selectbox(key="defect_length_basis").select(basis).run()
    app.number_input(key="cloth_width_mm").set_value(500.0).run()


result = {}
blank = AppTest.from_file("PWR110Calculator.py").run()
assert blank.session_state["calc_active"] is False
assert len(blank.metric) == len(blank.success) == len(blank.download_button) == 0
assert [element.value for element in blank.title] == ["🔧 PROWRAP ISO 24817 Calculator v1.2"]
result["blank"] = {"calc_active": False, "output": False, "v12_title": True}

actual = AppTest.from_file("PWR110Calculator.py").run()
fill(actual, basis="Actual defect length")
calculate_button(actual).click().run()
actual_text = text(actual)
assert not list(actual.exception) and not input_errors(actual)
for expected in ("**Defect Length Basis:** Actual defect length", "**B31G Candidates Assessed:** 1", "**Overall Repair-Zone Span:** 1000.0 mm", "**Governing Defect ID:** Actual/combined defect", "**B31G Assessment Length:** 1000.0 mm"):
    assert expected in actual_text
assert actual.metric[0].value == "12"
result["actual"] = {"b31g_mm": 1000.0, "span_mm": 1000.0, "governing": "Actual/combined defect", "plies": 12}

independent = AppTest.from_file("PWR110Calculator.py").run()
fill(independent, basis="Independent defects")
calculate_button(independent).click().run()
independent_text = text(independent)
assert not list(independent.exception) and not input_errors(independent)
for expected in ("**Defect Length Basis:** Independent defects", "**B31G Candidates Assessed:** 1", "**Overall Repair-Zone Span:** 1000.0 mm", "**Governing Defect ID:** Independent 10x10 mm defects", "**B31G Assessment Length:** 10.0 mm", "10 mm longitudinal by 10 mm circumferential"):
    assert expected in independent_text
assert independent.metric[0].value == "7"
result["independent"] = {"b31g_mm": 10.0, "span_mm": 1000.0, "assumption": "10x10 mm", "plies": 7}

manual = AppTest.from_file("PWR110Calculator.py").run()
fill(manual, basis="Enter manually")
manual.session_state["manual_defect_rows"] = [
    {"Defect ID": "D-01", "Individual longitudinal length [mm]": 10.0, "Remaining wall [mm]": 9.652, "Separation exceeds 3t": True},
    {"Defect ID": "D-02", "Individual longitudinal length [mm]": 35.0, "Remaining wall [mm]": 10.0, "Separation exceeds 3t": True},
]
manual.run()
calculate_button(manual).click().run()
manual_text = text(manual)
assert not list(manual.exception) and not input_errors(manual)
for expected in ("**Defect Length Basis:** Enter manually", "**B31G Candidates Assessed:** 2", "**Overall Repair-Zone Span:** 1000.0 mm", "**Governing Defect ID:** D-02", "**B31G Assessment Length:** 35.0 mm"):
    assert expected in manual_text
assert manual.metric[0].value == "7"
assert ["Defect ID", "B31G length [mm]", "Remaining wall [mm]", "Credited pressure [MPa]", "Governing"] in [list(element.value.columns) for element in manual.dataframe]
result["manual"] = {"candidates": 2, "governing": "D-02", "b31g_mm": 35.0, "span_mm": 1000.0, "plies": 7}

next(button for button in manual.button if button.label == "New / Clear Calculation").click().run()
assert manual.selectbox(key="type_").value == "Select…"
assert manual.session_state["defect_length_basis"] == "Select…"
assert manual.session_state["manual_defect_rows"] == []
assert manual.session_state["calc_active"] is False
assert len(manual.metric) == 0 and "Governing Defect ID" not in text(manual)
result["reset"] = {"mode": "Select…", "rows": 0, "calc_active": False, "stale_output": False}

for mechanism in ("Dent w/crack", "Dent no-crack"):
    app = AppTest.from_file("PWR110Calculator.py").run()
    app.session_state["defect_length_basis"] = "Unknown non-neutral basis"
    fill(app, mechanism=mechanism)
    assert [box for box in app.selectbox if box.key == "defect_length_basis"] == []
    calculate_button(app).click().run()
    rendered = text(app)
    assert not list(app.exception) and not input_errors(app)
    assert "Defect Length Basis" not in rendered and "B31G" not in rendered
    result[mechanism] = {"selector_visible": False, "injected_unknown_ignored": True, "calculated": True, "plies": int(app.metric[0].value)}

unknown_state = {
    "customer": "PROTAP", "location": "Turkey", "report_no": "V12-UNKNOWN",
    "od": 1016.0, "wall": 12.0, "yield_str": 450.0, "pres": 104.9,
    "temp": 40.0, "type_": "Corrosion", "loc_": "External",
    "len_": 1000.0, "rem_": 9.652, "corr_rate": None,
    "design_life": 20, "df": 0.72, "installation_temp": 20.0,
    "component_type": "Straight", "cyclic_derating_factor": 1.0,
    "axial_load_case": 0, "cloth_width_mm": 500.0,
    "defect_length_basis": "Unknown non-neutral basis", "manual_defect_rows": [],
}
precheck = missing_required_fields(unknown_state)
try:
    calculate_repair(customer="PROTAP", location="Turkey", report_no="V12-UNKNOWN", od=1016.0, wall=12.0, pressure=104.9, temp=40.0, defect_type="Corrosion", defect_loc="External", length=1000.0, rem_wall=9.652, yield_strength=450.0, design_factor=0.72, design_life=20, cloth_width_mm=500.0, defect_length_basis="Unknown non-neutral basis")
except ValueError as error:
    engine_error = str(error)
else:
    raise AssertionError("engine accepted unsupported basis")
assert precheck == []
assert engine_error == "Defect length basis must be one of the exact supported choices"
result["unknown_direct_state"] = {"form_precheck_missing": precheck, "engine_rejected": True, "error": engine_error, "ui_reachable": False}

print(json.dumps(result, sort_keys=True, separators=(",", ":")))
PY
```

Captured output (exit 0):

```json
{"Dent no-crack":{"calculated":true,"injected_unknown_ignored":true,"plies":18,"selector_visible":false},"Dent w/crack":{"calculated":true,"injected_unknown_ignored":true,"plies":42,"selector_visible":false},"actual":{"b31g_mm":1000.0,"governing":"Actual/combined defect","plies":12,"span_mm":1000.0},"blank":{"calc_active":false,"output":false,"v12_title":true},"independent":{"assumption":"10x10 mm","b31g_mm":10.0,"plies":7,"span_mm":1000.0},"manual":{"b31g_mm":35.0,"candidates":2,"governing":"D-02","plies":7,"span_mm":1000.0},"reset":{"calc_active":false,"mode":"Select\u2026","rows":0,"stale_output":false},"unknown_direct_state":{"engine_rejected":true,"error":"Defect length basis must be one of the exact supported choices","form_precheck_missing":[],"ui_reachable":false}}
```

### Parsed-PDF verifier

The complete calculation input set is declared in `base` and also emitted in
the captured JSON. The manual input adds D-01 `(10.0 mm, 9.652 mm, separated)`
and D-02 `(35.0 mm, 10.0 mm, separated)`.

Command:

```bash
python3 - 2>/dev/null <<'PY'
from io import BytesIO
import json
from pypdf import PdfReader
from PWR110Calculator import create_pdf
from corrosion_defects import ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS, ENTER_MANUALLY, IndividualCorrosionDefect
from prowrap_calculations import calculate_repair

base = {
    "customer": "PROTAP", "location": "Turkey", "report_no": "V12-PDF",
    "od": 1016.0, "wall": 12.0, "pressure": 104.9, "temp": 40.0,
    "defect_type": "Corrosion", "defect_loc": "External",
    "length": 1000.0, "rem_wall": 9.652, "yield_strength": 450.0,
    "design_factor": 0.72, "design_life": 20, "cloth_width_mm": 500.0,
}
routes = {
    "actual": (ACTUAL_DEFECT_LENGTH, ()),
    "independent": (INDEPENDENT_DEFECTS, ()),
    "manual": (ENTER_MANUALLY, (
        IndividualCorrosionDefect("D-01", 10.0, 9.652, True),
        IndividualCorrosionDefect("D-02", 35.0, 10.0, True),
    )),
}
common = [
    "PROWRAP COMPOSITE REPAIR REPORT - v1.2",
    "Overall Repair-Zone Span: 1000.0 mm",
    "3t Interaction Threshold: 36.0 mm",
    "B31G Candidates Assessed:", "Governing Defect:",
    "B31G Assessment Length:", "B31G Assessment Remaining Wall:",
    "Governing Credited Pressure:", "Continuous Repair Length (ISO):",
    "Required Plies:",
]
required = {
    "actual": [
        "Defect Length Basis: Actual defect length",
        "B31G Candidates Assessed: 1",
        "Governing Defect: Actual/combined defect",
        "B31G Assessment Length: 1000.0 mm",
        "B31G Assessment Remaining Wall: 9.652 mm",
        "The entered defect length represents a continuous or interacting corrosion feature.",
    ],
    "independent": [
        "Defect Length Basis: Independent defects",
        "B31G Candidates Assessed: 1",
        "Governing Defect: Independent 10x10 mm defects",
        "B31G Assessment Length: 10.0 mm",
        "B31G Assessment Remaining Wall: 9.652 mm",
        "Each corrosion defect is 10 mm longitudinal by 10 mm circumferential.",
        "Each corrosion defect is separated from every other defect by more than 36 mm (3t).",
        "Each corrosion defect uses the entered remaining wall.",
    ],
    "manual": [
        "Defect Length Basis: Enter manually",
        "B31G Candidates Assessed: 2", "Governing Defect: D-02",
        "B31G Assessment Length: 35.0 mm",
        "B31G Assessment Remaining Wall: 10.000 mm",
        "Each listed corrosion defect is separated from every other defect by more than 36 mm (3t).",
        "Individual B31G candidate assessments",
        "D-01: 10.0 mm, remaining wall 9.652 mm",
        "D-02: 35.0 mm, remaining wall 10.000 mm",
    ],
}
expected_totals = {"actual": 16, "independent": 18, "manual": 19}
output = {"inputs": base, "routes": {}}
for name, (basis, rows) in routes.items():
    report = calculate_repair(**base, defect_length_basis=basis, individual_defects=rows)
    pdf_bytes = create_pdf(report)
    assert pdf_bytes.startswith(b"%PDF")
    reader = PdfReader(BytesIO(pdf_bytes))
    parsed = "\n".join(page.extract_text() or "" for page in reader.pages)
    checks = common + required[name]
    missing = [field for field in checks if field not in parsed]
    assert len(checks) == expected_totals[name]
    assert len(reader.pages) == 2
    assert missing == []
    output["routes"][name] = {
        "asserted_fields": len(checks), "pages": len(reader.pages),
        "missing_count": len(missing), "mode": basis,
        "governing": report["governing_defect_id"],
        "b31g_mm": report["governing_b31g_length_mm"],
        "span_mm": report["repair_zone_length_mm"],
        "plies": report["num_plies"],
    }
print(json.dumps(output, sort_keys=True, separators=(",", ":")))
PY
```

Captured output (exit 0):

```json
{"inputs":{"cloth_width_mm":500.0,"customer":"PROTAP","defect_loc":"External","defect_type":"Corrosion","design_factor":0.72,"design_life":20,"length":1000.0,"location":"Turkey","od":1016.0,"pressure":104.9,"rem_wall":9.652,"report_no":"V12-PDF","temp":40.0,"wall":12.0,"yield_strength":450.0},"routes":{"actual":{"asserted_fields":16,"b31g_mm":1000.0,"governing":"Actual/combined defect","missing_count":0,"mode":"Actual defect length","pages":2,"plies":12,"span_mm":1000.0},"independent":{"asserted_fields":18,"b31g_mm":10.0,"governing":"Independent 10x10 mm defects","missing_count":0,"mode":"Independent defects","pages":2,"plies":7,"span_mm":1000.0},"manual":{"asserted_fields":19,"b31g_mm":35.0,"governing":"D-02","missing_count":0,"mode":"Enter manually","pages":2,"plies":7,"span_mm":1000.0}}}
```

### Direct installed-ply verifier

Command:

```bash
python3 - <<'PY'
import json
from corrosion_defects import ACTUAL_DEFECT_LENGTH, INDEPENDENT_DEFECTS
from prowrap_calculations import calculate_repair

base = dict(
    customer="PROTAP", location="Turkey", report_no="V12-PLIES",
    od=1016.0, wall=12.0, pressure=104.9, temp=40.0,
    defect_type="Corrosion", defect_loc="External", length=1000.0,
    rem_wall=9.652, yield_strength=450.0, design_factor=0.72,
    design_life=20, cloth_width_mm=500.0,
)
output = {}
for name, basis in (("Actual", ACTUAL_DEFECT_LENGTH), ("Independent", INDEPENDENT_DEFECTS)):
    result = calculate_repair(**base, defect_length_basis=basis)
    output[name] = {
        "installed_plies": result["num_plies"],
        "safe_substrate_mpa": result["p_steel_capacity"],
    }
assert output["Actual"]["installed_plies"] == 12
assert output["Independent"]["installed_plies"] == 7
print(json.dumps(output, sort_keys=True, separators=(",", ":")))
PY
```

Captured output (exit 0):

```json
{"Actual":{"installed_plies":12,"safe_substrate_mpa":7.571542406120033},"Independent":{"installed_plies":7,"safe_substrate_mpa":8.82257484144555}}
```
