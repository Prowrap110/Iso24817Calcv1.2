# PROWRAP v1.2 Independent Corrosion Verification

**Date:** 2026-08-19

**Repository:** isolated `Iso24817Calcv1.2` worktree

**Final-fix base HEAD:** `01e47cc784e13b24723d4bff74e119715eda1a05`
**Verdict:** The complete local v1.2 source release, including the final review
fixes, passes the fresh complete suite, focused engineering acceptance, desktop
release-contract tests, Streamlit route tests, and parsed/visual PDF checks. No
remote, push, deployment, distributable build, or CalcBatch-v1.2 creation was
performed.

## Fresh automated verification

### Complete suite

Command:

```bash
python3 -m unittest discover -v
```

Result: `Ran 150 tests in 2.078s` and `OK`.

| Passed | Failures | Errors | Skipped |
| ---: | ---: | ---: | ---: |
| 150 | 0 | 0 | 0 |

The recurring Streamlit bare-mode `missing ScriptRunContext` messages were
warnings only; the process exited 0.

### Focused engineering acceptance

Command:

```bash
python3 -m unittest -v test_v12_acceptance.py test_corrosion_defect_modes.py test_b31g.py test_typea_class3_adapter.py test_report_wording.py test_streamlit_form_submission.py
```

Result: `Ran 46 tests in 1.865s` and `OK`.

| Passed | Failures | Errors | Skipped |
| ---: | ---: | ---: | ---: |
| 46 | 0 | 0 | 0 |

### Final-fix focused regression set

Command:

```bash
python3 -m unittest -v test_packaging_contract.py test_desktop_launcher.py test_corrosion_defect_modes.py test_report_wording.py test_streamlit_form_submission.py test_corrosion_defects.py test_calculator_form.py
```

Result: `Ran 94 tests in 2.048s` and `OK`.

| Passed | Failures | Errors | Skipped |
| ---: | ---: | ---: | ---: |
| 94 | 0 | 0 | 0 |

## Distinct desktop release identity

The packaging contract, PyInstaller spec, build-script dry run, launcher test,
build guide, and employee install guide agree on these v1.2 identities:

| Surface | Verified v1.2 value |
| --- | --- |
| App bundle | `PROWRAP ISO 24817 Calculator v1.2.app` |
| Main executable | `PROWRAP ISO 24817 Calculator v1.2` |
| Bundle identifier | `com.protapglobal.prowrap.iso24817calculator.v12` |
| Archive | `PROWRAP-Calculator-v1.2-macOS-arm64-M4-M5.zip` |
| Launcher title | `PROWRAP ISO 24817 Calculator v1.2` |
| Internal version | `1.2` |
| Target architecture | arm64-only, M4/M5 release flow retained |

The distinct bundle path and identifier allow v1.2 to coexist with v1.1 rather
than replacing it. No app bundle was built, signed, notarized, installed, or
distributed during this source-verification wave.

## B31G method and applicability traceability

The engine still requests Modified B31G and preserves the existing Original
B31G fallback. The calculation basis is now derived from the governing
assessment actually returned, including its applicability.

| Case | SMYS | Actual method | Applicable | Safe substrate pressure | Displayed/PDF basis | Installed plies |
| --- | ---: | --- | --- | ---: | --- | ---: |
| Ordinary baseline | 359 MPa | Modified | yes | 9.951873620726573 MPa | `ASME B31G-2023 Level 1 (Modified)` | 3 |
| High-SMYS fallback | 555 MPa | Original | yes | 15.013693049770241 MPa | `ASME B31G-2023 Level 1 (Original)` | 3 |

The high-SMYS engine, Streamlit screen, and parsed PDF regressions all require
Original wording. The existing warning that Modified is unavailable above
483 MPa remains present, and the pressure value matches the direct Original
B31G assessment. A separate regression requires an inapplicable governing
candidate to report `outside applicability` and receive zero credit. Ordinary
eligible cases continue to report Modified.

## Mode-dependent length guidance

Streamlit AppTest verifies that `Defect Length Basis` remains immediately after
`Defect Length [mm]`, only for external corrosion, and that the guidance is
visible before calculation:

- Actual: the longitudinal length of the continuous or combined interacting
  flaw.
- Independent and Manual: the complete outer-to-outer repair-zone span for the
  overall continuous repair.

Dent routes continue to hide both the corrosion selector and this guidance.

## Manual-row normalization

Domain and form regressions verify that a completely blank data-editor
placeholder with an unchecked checkbox is ignored. Float NaN, pandas `NA`, and
`NaT` Defect IDs are treated as missing and cannot become accepted text such
as `nan`. A populated row with an unchecked separation box remains invalid and
the existing actionable `more than 3t` error is retained.

## PDF traceability and layout

The previously manual Actual, Independent, and Manual parsed-field checks now
run in `test_all_external_corrosion_pdf_routes_include_traceability_fields`.
They verify the v1.2 identity, mode, overall span, 3t threshold, candidate
count, governing ID and paired dimensions, governing credited pressure,
continuous repair length, plies, and route-specific assumptions.

Manual candidate assessments are a real bordered table with Defect ID, length,
remaining wall, actual method, applicability, credited pressure, and governing
status. A 28-row stress regression requires every ID, repeated table headers
after the page break, and an intact following installation checklist. The same
two-page stress report was rendered to PNG and visually inspected: columns and
rows were aligned and readable, the governing row was visible, and no section
was clipped or overlapped.

## 1016 mm numerical acceptance

Inputs common to the comparison were OD 1016 mm, nominal wall 12 mm, design
pressure 104.9 bar, remaining wall 9.652 mm, yield strength 450 MPa, design
factor 0.72, design life 20 years, overall repair-zone span 1000 mm, and 500 mm
cloth width.

| Route | B31G length | Safe substrate pressure | Installed plies | Continuous covered zone before overlap/taper |
| --- | ---: | ---: | ---: | ---: |
| Actual defect length | 1000 mm | 7.571542406120033 MPa | 12 | 1000 mm |
| Independent defects | 10 mm | 8.82257484144555 MPa | 7 | 1000 mm |
| Manual, governing D-02 | 35 mm | 8.783461911867068 MPa | 7 | 1000 mm |

The final fixes did not change these accepted numerical results.

## Repository isolation

- The v1.2 repository has no configured remote.
- The protected v1.1 worktree is clean at the required exact revision
  `7ca0e66ab4f8334fe07fda54b64599f54b1a1256`.
- The current CalcBatch worktree has no tracked or staged diff. Its pre-existing
  untracked `outputs/` directory remains preserved and uncommitted.
- No v1.1 or CalcBatch file, configuration, application, or deployment was
  changed.

## Remaining limitations and engineering boundary

- Independent and manual separation remain engineering assertions, not
  geometry automatically inferred by the calculator. Competent engineering
  review must confirm greater-than-3t separation and the applicability of the
  10 x 10 mm independent-pit model before issue.
- This is local source verification. It is not evidence of signing,
  notarization, installation on another Mac, publication, or deployment.

CalcBatch-v1.2 has not been created or modified in this phase. After the user
accepts the verified v1.2 calculator, create a separate CalcBatch-v1.2
repository and write a batch-specific specification using the verified v1.2
engine contract. Never modify or redeploy the current CalcBatch application.
