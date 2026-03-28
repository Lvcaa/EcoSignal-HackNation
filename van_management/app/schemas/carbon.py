from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.carbon.mappings import (
    DIRECT_ACTIVITY_TYPES,
    PERSONAL_FOOD_TO_ACTIVITY,
    PERSONAL_TRANSPORT_TO_ACTIVITY,
    WASTE_ACTIVITY_MATRIX,
    get_supported_units,
    get_supported_waste_treatments,
)
from app.carbon.personal_habits import get_personal_habit_template
from app.schemas.truck import TruckStateOut


class ActivityType(str, Enum):
    transport_car_petrol = "transport_car_petrol"
    transport_car_diesel = "transport_car_diesel"
    public_bus = "public_bus"
    train = "train"
    household_electricity = "household_electricity"
    water_usage = "water_usage"
    waste_collection_truck = "waste_collection_truck"
    food_beef = "food_beef"
    food_chicken = "food_chicken"
    food_seafood = "food_seafood"
    food_milk = "food_milk"
    food_eggs = "food_eggs"
    food_fruit = "food_fruit"
    food_vegetables = "food_vegetables"
    food_grains = "food_grains"
    food_legumes = "food_legumes"
    waste_plastic_recycled = "waste_plastic_recycled"
    waste_plastic_landfill = "waste_plastic_landfill"
    waste_paper_recycled = "waste_paper_recycled"
    waste_paper_landfill = "waste_paper_landfill"
    waste_glass_recycled = "waste_glass_recycled"
    waste_organic_composted = "waste_organic_composted"
    waste_organic_landfill = "waste_organic_landfill"
    waste_mixed_landfill = "waste_mixed_landfill"


class CalculationStatus(str, Enum):
    ok = "ok"
    needs_clarification = "needs_clarification"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"


class FootprintScope(str, Enum):
    personal = "personal"
    fleet = "fleet"


class CarbonEvaluationRequest(BaseModel):
    activity_type: ActivityType
    quantity: float = Field(..., gt=0)
    unit: str
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def validate_unit(self) -> "CarbonEvaluationRequest":
        allowed_units = get_supported_units(self.activity_type.value)
        if self.unit not in allowed_units:
            raise ValueError(
                f"Unsupported unit '{self.unit}' for activity_type "
                f"'{self.activity_type.value}'. Allowed: {', '.join(allowed_units)}"
            )
        return self


class CarbonBatchEvaluationRequest(BaseModel):
    evaluations: list[CarbonEvaluationRequest] = Field(..., min_length=1, max_length=500)


class CarbonEvaluationOut(BaseModel):
    scope: FootprintScope
    co2e_kg: float
    unit: str = "kgCO2e"
    source: str | None = None
    method: str
    activity_type: str
    emission_factor: float | None = None
    factor_unit: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel
    status: CalculationStatus
    timestamp: datetime
    input_quantity: float
    input_unit: str
    provider_factor_id: str | None = None
    provider_activity_id: str | None = None
    provider_data_version: str | None = None


class CarbonBatchEvaluationOut(BaseModel):
    accepted: int
    total_co2e_kg: float
    results: list[CarbonEvaluationOut]


class CarbonFactorMetadata(BaseModel):
    activity_type: str
    label: str
    category: str
    scope: FootprintScope
    allowed_units: list[str]
    parameter_kind: str
    selector: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    confidence: str
    notes: list[str] = Field(default_factory=list)


class CarbonFactorsOut(BaseModel):
    provider: str
    data_version: str
    factors: list[CarbonFactorMetadata]


class PersonalTransportMode(str, Enum):
    car_petrol = "car_petrol"
    car_diesel = "car_diesel"
    bus = "bus"
    train = "train"


class FoodCategory(str, Enum):
    beef = "beef"
    chicken = "chicken"
    seafood = "seafood"
    milk = "milk"
    eggs = "eggs"
    fruit = "fruit"
    vegetables = "vegetables"
    grains = "grains"
    legumes = "legumes"


class UtilityActivityType(str, Enum):
    household_electricity = "household_electricity"
    water_usage = "water_usage"


class PersonalWasteType(str, Enum):
    plastic = "plastic"
    paper = "paper"
    glass = "glass"
    organic = "organic"
    mixed = "mixed"


class PersonalHabitIn(BaseModel):
    habit_type: str = Field(..., min_length=1, max_length=64)
    count: float = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_habit_type(self) -> "PersonalHabitIn":
        try:
            get_personal_habit_template(self.habit_type)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        return self


class TransportHabitIn(BaseModel):
    mode: PersonalTransportMode
    distance_km: float = Field(..., gt=0)
    occupancy: int | None = Field(default=None, ge=1, le=12)

    @model_validator(mode="after")
    def validate_occupancy(self) -> "TransportHabitIn":
        if self.mode in {
            PersonalTransportMode.car_petrol,
            PersonalTransportMode.car_diesel,
        } and self.occupancy is None:
            raise ValueError("occupancy is required for private car modes")
        if self.mode in {PersonalTransportMode.bus, PersonalTransportMode.train} and self.occupancy is not None:
            raise ValueError("occupancy must not be sent for bus or train modes")
        return self


class FoodHabitIn(BaseModel):
    food_category: FoodCategory
    quantity: float = Field(..., gt=0)
    unit: str

    @model_validator(mode="after")
    def validate_unit(self) -> "FoodHabitIn":
        activity_type = PERSONAL_FOOD_TO_ACTIVITY[self.food_category.value]
        allowed_units = get_supported_units(activity_type)
        if self.unit not in allowed_units:
            raise ValueError(
                f"Unsupported unit '{self.unit}' for food_category "
                f"'{self.food_category.value}'. Allowed: {', '.join(allowed_units)}"
            )
        return self


class UtilityHabitIn(BaseModel):
    activity_type: UtilityActivityType
    quantity: float = Field(..., gt=0)
    unit: str

    @model_validator(mode="after")
    def validate_unit(self) -> "UtilityHabitIn":
        allowed_units = get_supported_units(self.activity_type.value)
        if self.unit not in allowed_units:
            raise ValueError(
                f"Unsupported unit '{self.unit}' for utility activity_type "
                f"'{self.activity_type.value}'. Allowed: {', '.join(allowed_units)}"
            )
        return self


class WasteHabitIn(BaseModel):
    waste_type: PersonalWasteType
    treatment: str
    quantity: float = Field(..., gt=0)
    unit: str

    @model_validator(mode="after")
    def validate_waste_combo(self) -> "WasteHabitIn":
        allowed = get_supported_waste_treatments(self.waste_type.value)
        if self.treatment not in allowed:
            raise ValueError(
                f"Unsupported treatment '{self.treatment}' for waste_type "
                f"'{self.waste_type.value}'. Allowed: {', '.join(allowed)}"
            )
        allowed_units = get_supported_units(
            WASTE_ACTIVITY_MATRIX[self.waste_type.value][self.treatment]
        )
        if self.unit not in allowed_units:
            raise ValueError(
                f"Unsupported unit '{self.unit}' for waste_type "
                f"'{self.waste_type.value}'. Allowed: {', '.join(allowed_units)}"
            )
        return self


class PersonalDailyFootprintRequest(BaseModel):
    person_id: str = Field(..., min_length=1, max_length=64)
    date: date
    transport: list[TransportHabitIn] = Field(default_factory=list)
    food: list[FoodHabitIn] = Field(default_factory=list)
    utilities: list[UtilityHabitIn] = Field(default_factory=list)
    waste: list[WasteHabitIn] = Field(default_factory=list)
    habits: list[PersonalHabitIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_at_least_one_item(self) -> "PersonalDailyFootprintRequest":
        if not any([self.transport, self.food, self.utilities, self.waste, self.habits]):
            raise ValueError(
                "At least one transport, food, utility, waste, or habit item is required"
            )
        return self


class PersonalEvaluatedItemOut(BaseModel):
    category: str
    label: str
    source_type: str | None = None
    source_key: str | None = None
    evaluation: CarbonEvaluationOut


class PersonalCategoryTotalsOut(BaseModel):
    transport: float = 0.0
    food: float = 0.0
    utilities: float = 0.0
    waste: float = 0.0


class PersonalDailyFootprintOut(BaseModel):
    scope: FootprintScope = FootprintScope.personal
    person_id: str
    date: date
    total_co2e_kg: float
    category_totals: PersonalCategoryTotalsOut
    items: list[PersonalEvaluatedItemOut]


class PersonalHabitComponentOut(BaseModel):
    activity_type: str
    quantity_per_occurrence: float
    unit: str
    label: str
    assumptions: list[str] = Field(default_factory=list)


class PersonalHabitTemplateOut(BaseModel):
    habit_type: str
    label: str
    category: str
    input_unit: str
    assumptions: list[str] = Field(default_factory=list)
    components: list[PersonalHabitComponentOut]


class PersonalHabitCatalogOut(BaseModel):
    habits: list[PersonalHabitTemplateOut]


class CarbonTruckSegmentOut(BaseModel):
    scope: FootprintScope = FootprintScope.fleet
    truck_id: str
    from_version: int
    to_version: int
    distance_km: float
    from_position_timestamp: datetime
    to_position_timestamp: datetime
    waste_type: str
    evaluation: CarbonEvaluationOut


class CarbonTruckDerivedOut(BaseModel):
    scope: FootprintScope = FootprintScope.fleet
    truck_id: str
    status: CalculationStatus
    latest_truck_state: TruckStateOut
    total_distance_km: float
    segment_count: int
    from_version: int | None = None
    to_version: int | None = None
    evaluation: CarbonEvaluationOut


class CarbonTruckHistoryOut(BaseModel):
    scope: FootprintScope = FootprintScope.fleet
    truck_id: str
    total: int
    page: int
    page_size: int
    total_distance_km: float
    total_co2e_kg: float
    records: list[CarbonTruckSegmentOut]
