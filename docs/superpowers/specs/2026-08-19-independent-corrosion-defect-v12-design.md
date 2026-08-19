# PROWRAP v1.2 Independent Corrosion Defect Design

**Date:** 2026-08-19

**Status:** Approved in conversation for specification and planning

**Target:** New `Iso24817Calcv1.2` repository and application

**Source baseline:** `Iso24817Calcv1.1` commit
`7ca0e66ab4f8334fe07fda54b64599f54b1a1256`

## 1. Objective

Create a new v1.2 calculator that distinguishes a continuous or interacting
corrosion feature from several independent corrosion defects. This prevents
the overall repair-zone span from being used automatically as the ASME B31G
longitudinal flaw length when the individual defects are genuinely
noninteracting.

The application continues to design one continuous composite repair. The
selected defect model may reduce the governing laminate thickness, but it does
not permit the repair to cover less than the complete outer-to-outer affected
axial span.

## 2. Isolation and release boundary

The existing v1.1 repository, GitHub application, Streamlit application, URL,
and calculation behavior shall remain unchanged.

The work shall be performed only in the new `Iso24817Calcv1.2` repository. The
new repository shall not have a push remote pointing to the v1.1 GitHub
repository. Any future GitHub repository and Streamlit application shall use a
new name and URL.

The existing CalcBatch repository and live batch application shall also remain
unchanged. A separate `CalcBatch-v1.2` project will be created only after the
v1.2 calculator has been implemented, tested, and accepted. The verified v1.2
calculation model will then be ported into that separate batch project.

## 3. Engineering basis

ASME B31G treats corrosion flaws within three nominal wall thicknesses (`3t`)
longitudinally or circumferentially as interacting. Interacting flaws are
evaluated as one combined flaw; noninteracting flaws may be evaluated
separately.

For this feature:

- `t` is the nominal pipe wall thickness, not remaining wall thickness.
- Separation confirmation is an engineering input supplied by the user.
- The calculator does not infer separation from photographs or inspection
  descriptions.
- The model applies only to external corrosion eligible for the existing B31G
  substrate-credit route.
- Dent, crack, leak, internal-corrosion, and Type B routing remain unchanged.

## 4. User interface

For `Mechanism = Corrosion` and `Location = External`, place a new selection
immediately after `Defect Length [mm]`:

**Defect Length Basis**

1. `Actual defect length`
2. `Independent defects`
3. `Enter manually`

For other mechanisms or locations, the selector is hidden and the calculator
uses the existing length behavior.

The existing `Defect Length [mm]` input has mode-dependent help text:

- `Actual defect length`: longitudinal length of the continuous or combined
  interacting flaw.
- `Independent defects`: complete outer-to-outer axial span to be covered by
  the continuous repair.
- `Enter manually`: complete outer-to-outer axial span to be covered by the
  continuous repair.

### 4.1 Actual defect length

Display the existing `Remaining Wall [mm]` input. Use the existing inputs
without changing the current calculation:

- B31G length = entered defect length.
- B31G remaining wall = entered remaining wall.
- Repair-zone length = entered defect length.

The report wording shall identify this as a continuous or interacting-defect
assessment. It shall not describe the B31G result as exaggerated.

### 4.2 Independent defects

Display the existing `Remaining Wall [mm]` input and a permanent assumption
notice:

- every defect is 10 mm longitudinal by 10 mm circumferential;
- every defect is separated from every other defect by more than `3t`;
- every defect has the entered remaining wall;
- the entered Defect Length is the overall repair-zone span.

Use 10 mm as the B31G longitudinal length. The 10 mm circumferential width is
reported as an assumption but is not an input to the Level 1 B31G equation.
The number of identical independent defects is not needed for laminate
thickness or continuous repair length and therefore is not requested.

Selecting this option is the user's affirmative engineering confirmation of
the stated assumptions. The selection alone does not create a review warning,
but the assumptions must remain visible in the screen result and PDF report.

### 4.3 Enter manually

Hide the single `Remaining Wall [mm]` input and display a dynamic editable
table with these exact columns:

| Column | Type | Requirement |
|---|---|---|
| Defect ID | text | required and unique |
| Individual longitudinal length [mm] | number | required and greater than zero |
| Remaining wall [mm] | number | required, zero or greater, and no greater than nominal wall |
| Separation exceeds 3t | checkbox | must be confirmed for every defect |

The table supports adding and deleting rows. At least one complete row is
required. Blank placeholder rows are ignored; partially populated rows are
input errors.

The interface shows the calculated `3t` threshold beside the table. If any
defect is not confirmed as separated by more than `3t`, calculation stops with
an input error directing the user to combine interacting defects and use
`Actual defect length`.

## 5. Calculation model

Introduce two separate length concepts throughout the calculation:

- `repair_zone_length_mm`: the complete axial span used for ISO repair length,
  band procurement, fabric, and epoxy.
- `b31g_length_mm`: the longitudinal length used for one B31G assessment.

Represent each B31G candidate as a paired individual defect containing its ID,
longitudinal length, and remaining wall. Depth and length from different
defects shall never be combined in manual mode.

### 5.1 Candidate construction

- `Actual defect length`: one candidate using the entered length and remaining
  wall.
- `Independent defects`: one representative candidate with ID
  `Independent 10x10 mm defects`, length 10 mm, and the entered remaining wall.
- `Enter manually`: one candidate for every complete table row.

### 5.2 B31G assessment and governing defect

Run the existing Modified B31G assessment independently for every candidate,
including the current safety factor and Original B31G fallback rules.

For each candidate:

- credited pressure is its calculated safe pressure when B31G is applicable;
- credited pressure is zero when B31G is not applicable;
- a remaining wall below 1 mm retains the existing no-substrate-capacity and
  Type B behavior.

The governing candidate is the candidate with the lowest credited substrate
pressure. Use that pressure in the existing ISO 24817 laminate equations. A
stable input-order tie break is used when candidates have equal credited
pressure.

For manual mode, the overall minimum remaining wall is retained separately for
wall-loss reporting, no-substrate-capacity checks, and conservative supporting
checks. The governing defect ID, its paired length and remaining wall, and all
individual B31G assessments are retained in the result model.

### 5.3 Continuous repair length

All three modes use the existing ISO repair-length equation:

```text
total repair length
  = repair zone length
  + 2 x required terminal overlap
  + 2 x taper length
```

The governing installed ply count is applied over this complete continuous
repair length. Independent mode does not replace the overall span with 10 mm
when calculating coverage, band count, fabric, epoxy, or procurement length.

### 5.4 Optional Type A / Class 3 check

When requested and otherwise eligible, pass the governing substrate pressure
and the conservative minimum remaining wall into the existing optional Type A
/ Class 3 check. Existing noncontrolling and warning behavior remains
unchanged.

## 6. Result and PDF reporting

The screen and PDF shall report:

- selected Defect Length Basis;
- overall repair-zone span;
- `3t` threshold for the nominal wall;
- number of B31G candidates assessed;
- governing Defect ID;
- governing B31G longitudinal length;
- governing B31G remaining wall;
- governing safe substrate pressure;
- continuous-repair length and installed plies;
- the permanent 10 x 10 mm assumptions when independent mode is selected;
- a compact individual-defect assessment table in manual mode.

Existing B31G details, warnings, calculation-basis wording, and preliminary
engineering disclaimer remain present.

## 7. Validation and safe behavior

The calculator rejects:

- a missing length-basis selection for eligible external corrosion;
- an independent-mode repair-zone span below 10 mm;
- a manual table with no complete defects;
- duplicate or blank manual Defect IDs;
- nonnumeric, nonfinite, zero, or negative individual lengths;
- an individual length greater than the overall repair-zone span;
- a remaining wall below zero or above nominal wall;
- a blank or false separation confirmation;
- partially populated manual rows.

Errors are shown as input errors and no report is generated from invalid data.
The calculator never silently converts an unconfirmed interacting group into
independent defects.

## 8. Compatibility

The calculation function receives new optional arguments whose defaults
reproduce v1.1 behavior:

- default basis: `Actual defect length`;
- default manual-defect collection: empty;
- existing `length` and `rem_wall` calls continue to work unchanged.

Existing v1.1 regression cases copied into the v1.2 repository must remain
green. Existing blank-on-opening behavior is retained, including clearing the
new selection and manual table through `New / Clear Calculation`.

## 9. Test and acceptance requirements

Tests shall cover at least:

1. Exact v1.1 numerical baseline under `Actual defect length`.
2. Independent mode produces the same B31G pressure and plies as a direct
   10 mm flaw with the entered remaining wall.
3. Independent mode retains the overall span in total repair length and
   material quantities.
4. Manual mode evaluates every paired length and remaining wall and selects the
   lowest credited pressure.
5. Manual mode does not combine the longest length from one defect with the
   lowest remaining wall from another.
6. A nonapplicable manual defect governs with zero substrate credit.
7. Empty, partial, duplicate, out-of-range, and unconfirmed manual rows fail
   safely.
8. Nonexternal-corrosion mechanisms retain their existing routes.
9. The optional Type A / Class 3 check receives the governing pressure and
   conservative minimum wall.
10. Screen and PDF show the mode, assumptions, governing defect, and repair
    span correctly.
11. New calculation/reset clears all new state.
12. The complete inherited and new test suite passes.

Acceptance shall include a numerical side-by-side case using the same pipe and
overall repair span in all three modes, demonstrating that B31G thickness uses
the selected defect model while continuous repair length continues to use the
overall span.

## 10. CalcBatch-v1.2 follow-on boundary

After v1.2 acceptance, create a separate `CalcBatch-v1.2` repository from the
current batch baseline. Do not revise the current CalcBatch repository or live
application.

The follow-on batch design will preserve one main result row per continuous
repair. It will add the same three mode choices and an `Individual Defects`
worksheet linked to manual-mode main rows by a stable Repair Group ID. Current
seven-sheet workbooks will be accepted as legacy inputs and upgraded with
`Actual defect length` as their explicit default. A separate detailed batch
specification and implementation plan will be reviewed after the v1.2 engine
has been verified.
