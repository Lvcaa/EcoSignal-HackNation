from dataclasses import dataclass

from app.carbon.mappings import get_mapping


@dataclass(frozen=True)
class HabitComponent:
    activity_type: str
    quantity_per_occurrence: float
    unit: str
    label: str
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True)
class PersonalHabitTemplate:
    habit_type: str
    label: str
    category: str
    input_unit: str
    assumptions: tuple[str, ...]
    components: tuple[HabitComponent, ...]


PERSONAL_HABIT_TEMPLATES: dict[str, PersonalHabitTemplate] = {
    "shower": PersonalHabitTemplate(
        habit_type="shower",
        label="Standard shower",
        category="utilities",
        input_unit="count",
        assumptions=(
            "One shower is modeled as 60 liters of water usage.",
            "One shower is modeled as 2.1 kWh of energy for hot water heating.",
        ),
        components=(
            HabitComponent(
                activity_type="water_usage",
                quantity_per_occurrence=0.06,
                unit="m3",
                label="water",
            ),
            HabitComponent(
                activity_type="household_electricity",
                quantity_per_occurrence=2.1,
                unit="kWh",
                label="heating_energy",
            ),
        ),
    ),
    "washing_machine": PersonalHabitTemplate(
        habit_type="washing_machine",
        label="Standard washing machine cycle",
        category="utilities",
        input_unit="count",
        assumptions=(
            "One washing machine cycle is modeled as 50 liters of water usage.",
            "One washing machine cycle is modeled as 0.75 kWh of electricity.",
        ),
        components=(
            HabitComponent(
                activity_type="water_usage",
                quantity_per_occurrence=0.05,
                unit="m3",
                label="water",
            ),
            HabitComponent(
                activity_type="household_electricity",
                quantity_per_occurrence=0.75,
                unit="kWh",
                label="electricity",
            ),
        ),
    ),
}


def get_personal_habit_template(habit_type: str) -> PersonalHabitTemplate:
    try:
        template = PERSONAL_HABIT_TEMPLATES[habit_type]
    except KeyError as exc:
        raise KeyError(f"Unsupported personal habit_type '{habit_type}'") from exc

    for component in template.components:
        mapping = get_mapping(component.activity_type)
        if mapping.scope != "personal":
            raise RuntimeError(
                f"Personal habit '{habit_type}' references non-personal activity "
                f"'{component.activity_type}'"
            )
    return template


def list_personal_habit_templates() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for template in PERSONAL_HABIT_TEMPLATES.values():
        rows.append(
            {
                "habit_type": template.habit_type,
                "label": template.label,
                "category": template.category,
                "input_unit": template.input_unit,
                "assumptions": list(template.assumptions),
                "components": [
                    {
                        "activity_type": component.activity_type,
                        "quantity_per_occurrence": component.quantity_per_occurrence,
                        "unit": component.unit,
                        "label": component.label,
                        "assumptions": list(component.assumptions),
                    }
                    for component in template.components
                ],
            }
        )
    return rows

