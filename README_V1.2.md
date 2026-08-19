# PROWRAP ISO 24817 Calculator v1.2

## Purpose and release boundary

Version 1.2 is an isolated local calculator release for preliminary screening
of **external corrosion** repairs.  It adds a deliberate choice for how the
corrosion feature is assessed for B31G pressure credit.  It does not replace
competent engineering review, inspection data, a repair procedure, or the
applicable pipeline operator's approval.

This work does not overwrite, rename, redeploy, or otherwise change the
existing **Iso24817Calcv1.1** calculator or the current **CalcBatch** project,
repository, name, or URL.  No deployment is claimed by this document.  A
future **CalcBatch-v1.2** is a separate project and may only port this accepted
v1.2 engine after acceptance; it is not the current CalcBatch.

## Choose the defect-length basis

The **Defect Length Basis** control is shown only for an external corrosion
calculation.  Select exactly one of these choices after the inspection data
and corrosion interaction assessment have been reviewed.

### Actual defect length

Use this when the entered **Defect Length [mm]** is one continuous corrosion
feature, or when nearby corrosion features interact and must be treated as one
combined feature.  The entered length is used for both the B31G assessment and
the repair-zone span.  This is the v1.1-compatible default: leaving the new
choice at **Actual defect length** reproduces the v1.1 calculation route.

### Independent defects

Use this only when competent engineering review confirms that every relevant
corrosion feature is independent: each is separated from every other relevant
feature by **more than 3t**.  Here `t` means the **nominal pipe wall**, not the
remaining wall, corrosion depth, or laminate thickness.  For example, a
12 mm nominal wall gives a threshold of more than 36 mm.

This mode is an engineering assumption, not an automatic conclusion from a
photograph, scan, or a visual gap.  It assumes every assessed pit is **10 mm
longitudinal by 10 mm circumferential**, and applies the entered **Remaining
Wall [mm]** to each pit.  The B31G calculation therefore uses a 10 mm
longitudinal length.  The entered **Defect Length [mm]** still means the full
outer-to-outer repair-zone span, not 10 mm.

### Enter manually

Use this when the inspection and engineering review have identified individual
defects with different longitudinal lengths and/or remaining walls.  Complete
the table for every assessed defect:

| Column | Operator action |
| --- | --- |
| Defect ID | Enter a unique, traceable inspection identifier. |
| Individual longitudinal length [mm] | Enter that defect's measured longitudinal B31G length. |
| Remaining wall [mm] | Enter that defect's measured remaining wall. |
| Separation exceeds 3t | Confirm the defect is more than `3 × nominal wall` from every other listed defect. |

The calculator preserves each length/remaining-wall pair.  It calculates a
B31G candidate for each row; the row with the lowest credited pressure governs
the result (where credits are equal, the first listed row governs).  The
entered **Defect Length [mm]** remains the complete repair-zone span.

Do not calculate from a partly completed table.  A blank ID, length, wall,
separation confirmation, duplicate ID, non-positive length, wall outside the
nominal-wall range, or an unconfirmed `>3t` separation is invalid.  The app
stops and displays an input error; correct or obtain the missing inspection
and engineering confirmation before proceeding.

## B31G assessment length and repair coverage

The B31G assessment length and the installed repair length serve different
purposes:

- **B31G assessment length** is the length used to calculate pressure credit:
  the entered defect length for Actual defect length, 10 mm for Independent
  defects, or each manual row's individual longitudinal length.
- **Overall repair-zone span** is always the entered **Defect Length [mm]**.
  The calculated ISO repair length includes this entire span plus the required
  overlap and taper at both ends.  One continuous repair covers the complete
  outer-to-outer span; independent B31G pits do not permit gaps in that repair
  zone.

Review the result/PDF before issue.  Confirm the displayed Defect Length Basis,
Overall Repair-Zone Span, B31G Assessment Length, Governing Defect (manual
mode), credited pressure, ply count, overlap, taper, and total ISO repair
length agree with the inspection record and approved repair plan.

## Local operation and verification

From the isolated v1.2 repository root, create a local environment and run the
calculator:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/streamlit run PWR110Calculator.py
```

For numerical acceptance, run:

```bash
python3 -m unittest -v test_v12_acceptance.py
python3 -m unittest discover -v
```

The side-by-side acceptance case checks a common 1,000 mm repair zone.  Actual
defect length uses its full 1,000 mm B31G length, Independent defects uses the
10 mm assumption, and manual input keeps its two entered pairs.  All three
results must retain 1,000 mm of continuous coverage before overlap and taper.

For a packaged employee build, follow [DESKTOP_BUILD.md](DESKTOP_BUILD.md) and
[EMPLOYEE_MAC_INSTALL.md](EMPLOYEE_MAC_INSTALL.md).  Packaging and local
operation do not authorize publishing, deployment, or changes to v1.1 or the
current CalcBatch.

## Engineering responsibility

This is a preliminary ISO 24817 / ASME PCC-2 screening estimate that uses an
ASME B31G Level 1 (Modified) substrate assessment where applicable.  The
operator is responsible for selecting the appropriate mode only from verified
inspection data and for escalating uncertain, interacting, clustered, or
out-of-scope corrosion to competent engineering review.  The `>3t` assertion,
the 10 x 10 mm independent-pit model, and the stated repair-zone span must be
recorded and accepted by the responsible engineer before the calculation is
used to support a repair decision.
