from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping

import pandas as pd


ACTUAL_DEFECT_LENGTH = "Actual defect length"
INDEPENDENT_DEFECTS = "Independent defects"
ENTER_MANUALLY = "Enter manually"
DEFECT_LENGTH_BASES = (
    ACTUAL_DEFECT_LENGTH,
    INDEPENDENT_DEFECTS,
    ENTER_MANUALLY,
)
INDEPENDENT_PIT_LONGITUDINAL_MM = 10.0
INDEPENDENT_PIT_CIRCUMFERENTIAL_MM = 10.0
INTERACTION_DISTANCE_MULTIPLIER = 3.0

_MANUAL_ROW_FIELDS = (
    "Defect ID",
    "Individual longitudinal length [mm]",
    "Remaining wall [mm]",
    "Separation exceeds 3t",
)


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


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a finite number") from error
    if not isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    try:
        return bool(missing)
    except (TypeError, ValueError):
        return False


def normalize_manual_defects(
    records: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
) -> tuple[IndividualCorrosionDefect, ...]:
    defects = []
    for row_number, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            raise ValueError(f"manual defect row {row_number} must be a record")
        values = tuple(record.get(field) for field in _MANUAL_ROW_FIELDS)
        defect_id, length, wall, separation = values
        if (
            all(_blank(value) for value in (defect_id, length, wall))
            and (_blank(separation) or separation is False)
        ):
            continue

        if _blank(defect_id):
            raise ValueError("Defect ID is required")
        if _blank(length):
            raise ValueError("individual longitudinal length is required")
        if _blank(wall):
            raise ValueError("remaining wall is required")
        if _blank(separation):
            raise ValueError("separation confirmation is required")
        if not isinstance(defect_id, str):
            defect_id = str(defect_id)
        if not isinstance(separation, bool):
            raise ValueError("Separation exceeds 3t must be a checkbox value")
        defects.append(
            IndividualCorrosionDefect(
                defect_id=defect_id.strip(),
                longitudinal_length_mm=_finite_number(
                    length, "individual longitudinal length"
                ),
                remaining_wall_mm=_finite_number(wall, "remaining wall"),
                separation_exceeds_3t=separation,
            )
        )
    return tuple(defects)


def _validate_candidate(
    defect: IndividualCorrosionDefect,
    *,
    repair_zone_length_mm: float,
    nominal_wall_mm: float,
) -> IndividualCorrosionDefect:
    if not isinstance(defect.defect_id, str) or not defect.defect_id.strip():
        raise ValueError("Defect ID is required")
    length = _finite_number(defect.longitudinal_length_mm, "individual longitudinal length")
    wall = _finite_number(defect.remaining_wall_mm, "remaining wall")
    if length <= 0:
        raise ValueError("individual longitudinal length must be greater than zero")
    if length > repair_zone_length_mm:
        raise ValueError("individual longitudinal length cannot exceed repair-zone length")
    if wall < 0:
        raise ValueError("remaining wall must be zero or greater")
    if wall > nominal_wall_mm:
        raise ValueError("remaining wall cannot exceed nominal wall")
    if defect.separation_exceeds_3t is not True:
        raise ValueError(
            "Each defect must be confirmed as separated by more than 3t"
        )
    return IndividualCorrosionDefect(defect.defect_id.strip(), length, wall, True)


def build_corrosion_assessment_plan(
    *,
    basis: str,
    repair_zone_length_mm: float,
    nominal_wall_mm: float,
    default_remaining_wall_mm: float | None,
    manual_defects: tuple[IndividualCorrosionDefect, ...] = (),
) -> CorrosionAssessmentPlan:
    if basis not in DEFECT_LENGTH_BASES:
        raise ValueError("Defect length basis must be one of the exact supported choices")

    repair_zone_length = _finite_number(repair_zone_length_mm, "repair-zone length")
    nominal_wall = _finite_number(nominal_wall_mm, "nominal wall")
    if repair_zone_length <= 0:
        raise ValueError("repair-zone length must be greater than zero")
    if nominal_wall <= 0:
        raise ValueError("nominal wall must be greater than zero")

    interaction_distance = INTERACTION_DISTANCE_MULTIPLIER * nominal_wall
    if basis == ENTER_MANUALLY:
        candidates = tuple(
            _validate_candidate(
                defect,
                repair_zone_length_mm=repair_zone_length,
                nominal_wall_mm=nominal_wall,
            )
            for defect in manual_defects
        )
        if not candidates:
            raise ValueError("At least one complete manual defect row is required")
        defect_ids = [defect.defect_id for defect in candidates]
        if len(set(defect_ids)) != len(defect_ids):
            raise ValueError("Defect ID must be unique")
        assumptions = (
            "Each listed corrosion defect is separated from every other defect by more than "
            f"{interaction_distance:g} mm (3t).",
        )
    else:
        remaining_wall = _finite_number(
            default_remaining_wall_mm, "remaining wall"
        )
        if remaining_wall < 0:
            raise ValueError("remaining wall must be zero or greater")
        if remaining_wall > nominal_wall:
            raise ValueError("remaining wall cannot exceed nominal wall")
        if basis == ACTUAL_DEFECT_LENGTH:
            candidates = (
                IndividualCorrosionDefect(
                    "Actual/combined defect",
                    repair_zone_length,
                    remaining_wall,
                    True,
                ),
            )
            assumptions = (
                "The entered defect length represents a continuous or interacting corrosion feature.",
            )
        else:
            if repair_zone_length < INDEPENDENT_PIT_LONGITUDINAL_MM:
                raise ValueError("repair-zone length must be at least 10 mm")
            candidates = (
                IndividualCorrosionDefect(
                    "Independent 10x10 mm defects",
                    INDEPENDENT_PIT_LONGITUDINAL_MM,
                    remaining_wall,
                    True,
                ),
            )
            assumptions = (
                "Each corrosion defect is 10 mm longitudinal by 10 mm circumferential.",
                "Each corrosion defect is separated from every other defect by more than "
                f"{interaction_distance:g} mm (3t).",
                "Each corrosion defect uses the entered remaining wall.",
            )

    return CorrosionAssessmentPlan(
        basis=basis,
        repair_zone_length_mm=repair_zone_length,
        interaction_distance_mm=interaction_distance,
        candidates=candidates,
        minimum_remaining_wall_mm=min(
            defect.remaining_wall_mm for defect in candidates
        ),
        assumptions=assumptions,
    )
