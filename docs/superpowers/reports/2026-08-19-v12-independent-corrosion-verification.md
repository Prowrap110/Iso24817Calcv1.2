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
