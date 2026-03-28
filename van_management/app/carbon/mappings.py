from dataclasses import dataclass, field
from typing import Literal

ParameterKind = Literal[
    "distance",
    "energy",
    "passenger_over_distance",
    "volume",
    "weight",
]
FootprintScope = Literal["personal", "fleet"]


@dataclass(frozen=True)
class CarbonMapping:
    activity_type: str
    label: str
    category: str
    scope: FootprintScope
    parameter_kind: ParameterKind
    allowed_units: tuple[str, ...]
    selector: dict[str, str | int]
    assumptions: tuple[str, ...] = ()
    confidence: str = "high"
    notes: tuple[str, ...] = ()

    @property
    def canonical_unit(self) -> str:
        if self.parameter_kind == "passenger_over_distance":
            return "passenger_km"
        return self.allowed_units[0]


ACTIVITY_MAPPINGS: dict[str, CarbonMapping] = {
    "transport_car_petrol": CarbonMapping(
        activity_type="transport_car_petrol",
        label="Private car (petrol, medium profile)",
        category="transport",
        scope="personal",
        parameter_kind="distance",
        allowed_units=("km",),
        selector={
            "activity_id": (
                "passenger_vehicle-vehicle_type_medium_car-"
                "fuel_source_petrol-engine_size_gt_1.6l_lt_2l-"
                "vehicle_age_na-vehicle_weight_gt_950kg_lt_1350kg"
            ),
            "source": "CO2 Emissiefactoren",
            "region": "NL",
            "year": 2025,
            "source_lca_activity": "well_to_wheel",
        },
        assumptions=(
            "Pinned to a medium private petrol car profile from CO2 Emissiefactoren 2025.",
        ),
    ),
    "transport_car_diesel": CarbonMapping(
        activity_type="transport_car_diesel",
        label="Private car (diesel, medium profile)",
        category="transport",
        scope="personal",
        parameter_kind="distance",
        allowed_units=("km",),
        selector={
            "activity_id": (
                "passenger_vehicle-vehicle_type_medium_car-"
                "fuel_source_diesel-engine_size_gt_1.8l_lt_2.2l-"
                "vehicle_age_na-vehicle_weight_gt_1050kg_lt_1450kg"
            ),
            "source": "CO2 Emissiefactoren",
            "region": "NL",
            "year": 2025,
            "source_lca_activity": "well_to_wheel",
        },
        assumptions=(
            "Pinned to a medium private diesel car profile from CO2 Emissiefactoren 2025.",
        ),
    ),
    "public_bus": CarbonMapping(
        activity_type="public_bus",
        label="Public bus (diesel)",
        category="transport",
        scope="personal",
        parameter_kind="passenger_over_distance",
        allowed_units=("passenger_km",),
        selector={
            "activity_id": (
                "passenger_vehicle-vehicle_type_local_bus_not_london-"
                "fuel_source_na-distance_na-engine_size_na"
            ),
            "source": "BEIS",
            "region": "GB",
            "year": 2025,
            "source_lca_activity": "fuel_combustion",
        },
        assumptions=(
            "Pinned to the BEIS 2025 local bus (not London) passenger factor.",
        ),
    ),
    "train": CarbonMapping(
        activity_type="train",
        label="Passenger train",
        category="transport",
        scope="personal",
        parameter_kind="passenger_over_distance",
        allowed_units=("passenger_km",),
        selector={
            "activity_id": "passenger_train-route_type_na-fuel_source_na",
            "source": "CO2 Emissiefactoren",
            "region": "NL",
            "year": 2025,
            "source_lca_activity": "well_to_wheel",
        },
        assumptions=(
            "Pinned to the Dutch average train factor for 2025.",
        ),
    ),
    "household_electricity": CarbonMapping(
        activity_type="household_electricity",
        label="Household electricity",
        category="utilities",
        scope="personal",
        parameter_kind="energy",
        allowed_units=("kWh",),
        selector={
            "activity_id": "electricity-supply_grid-source_total_supplier_mix",
            "source": "AIB",
            "region": "IT",
            "year": 2024,
            "source_lca_activity": "electricity_generation",
        },
        assumptions=(
            "Pinned to Italy total supplier mix electricity from the 2024 European Residual Mix data.",
            "The source is marked by Climatiq as a partial factor that includes CO2 only.",
        ),
    ),
    "water_usage": CarbonMapping(
        activity_type="water_usage",
        label="Water supply",
        category="utilities",
        scope="personal",
        parameter_kind="volume",
        allowed_units=("m3", "l"),
        selector={
            "activity_id": "water_supply-type_na",
            "source": "BEIS",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "upstream",
        },
        assumptions=(
            "Pinned to the BEIS 2024 water supply factor because it is deterministic and volume-based.",
        ),
    ),
    "waste_collection_truck": CarbonMapping(
        activity_type="waste_collection_truck",
        label="Waste collection truck proxy",
        category="fleet",
        scope="fleet",
        parameter_kind="distance",
        allowed_units=("km",),
        selector={
            "activity_id": (
                "commercial_vehicle-vehicle_type_truck_light-"
                "fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"
            ),
            "source": "EPA",
            "region": "US",
            "year": 2025,
            "source_lca_activity": "use_phase",
        },
        assumptions=(
            "Pinned to the EPA 2025 light-duty truck factor as a proxy for waste collection vans.",
            "Truck-derived calculations use straight-line distance between stored GPS points.",
        ),
        confidence="medium",
    ),
    "food_beef": CarbonMapping(
        activity_type="food_beef",
        label="Food category: beef",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_beef",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
    ),
    "food_chicken": CarbonMapping(
        activity_type="food_chicken",
        label="Food category: chicken",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_chicken_breast_flesh_and_skin_raw",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
    ),
    "food_seafood": CarbonMapping(
        activity_type="food_seafood",
        label="Food category: seafood",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_mussel_raw",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
        assumptions=(
            "The generic seafood category is pinned to mussels as the representative factor.",
        ),
    ),
    "food_milk": CarbonMapping(
        activity_type="food_milk",
        label="Food category: milk",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "consumer_goods-type_milk",
            "source": "GEMIS",
            "region": "DE",
            "year": 2015,
            "source_lca_activity": "cradle_to_shelf",
        },
    ),
    "food_eggs": CarbonMapping(
        activity_type="food_eggs",
        label="Food category: eggs",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "consumer_goods-type_eggs-origin_region_global",
            "source": "WRAP",
            "region": "GLOBAL",
            "year": 2018,
            "source_lca_activity": "cradle_to_processing_gate",
        },
    ),
    "food_fruit": CarbonMapping(
        activity_type="food_fruit",
        label="Food category: fruit",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_banana_raw",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
        assumptions=(
            "The generic fruit category is pinned to bananas as the representative factor.",
        ),
    ),
    "food_vegetables": CarbonMapping(
        activity_type="food_vegetables",
        label="Food category: vegetables",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_carrot_raw",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
        assumptions=(
            "The generic vegetables category is pinned to carrots as the representative factor.",
        ),
    ),
    "food_grains": CarbonMapping(
        activity_type="food_grains",
        label="Food category: grains",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_rice_red_raw",
            "source": "Agribalyse",
            "region": "FR",
            "year": 2024,
            "source_lca_activity": "total",
        },
        assumptions=(
            "The generic grains category is pinned to red rice as the representative factor.",
        ),
    ),
    "food_legumes": CarbonMapping(
        activity_type="food_legumes",
        label="Food category: legumes",
        category="food",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "food-type_beans_soy_dried_raw",
            "source": "CONCITO and 2-0 LCA",
            "region": "GB",
            "year": 2024,
            "source_lca_activity": "total",
        },
        assumptions=(
            "The generic legumes category is pinned to dried soy beans as the representative factor.",
        ),
    ),
    "waste_plastic_recycled": CarbonMapping(
        activity_type="waste_plastic_recycled",
        label="Waste: plastic recycled",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": (
                "waste_management-type_plastic_mixed_recycled_"
                "treatment_of_waste_polyethylene_recycling-disposal_method_recycling"
            ),
            "source": "ecoinvent",
            "region": "ECOINVENT_EUROPE",
            "year": 2021,
        },
        confidence="medium",
    ),
    "waste_plastic_landfill": CarbonMapping(
        activity_type="waste_plastic_landfill",
        label="Waste: plastic landfill",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_plastics-disposal_method_landfill",
            "source": "BEIS",
            "region": "GB",
            "year": 2025,
        },
        confidence="medium",
    ),
    "waste_paper_recycled": CarbonMapping(
        activity_type="waste_paper_recycled",
        label="Waste: paper recycled",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_paper_and_cardboard-disposal_method_recycled",
            "source": "EPA",
            "region": "US",
            "year": 2025,
        },
        confidence="medium",
    ),
    "waste_paper_landfill": CarbonMapping(
        activity_type="waste_paper_landfill",
        label="Waste: paper landfill",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_paper_and_cardboard-disposal_method_landfill",
            "source": "EPA",
            "region": "US",
            "year": 2025,
        },
        confidence="medium",
    ),
    "waste_glass_recycled": CarbonMapping(
        activity_type="waste_glass_recycled",
        label="Waste: glass recycled",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_glass-disposal_method_recycled",
            "source": "EPA",
            "region": "US",
            "year": 2025,
        },
        confidence="medium",
    ),
    "waste_organic_composted": CarbonMapping(
        activity_type="waste_organic_composted",
        label="Waste: organic composted",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_food_waste-disposal_method_composting",
            "source": "BEIS",
            "region": "GB",
            "year": 2025,
        },
        confidence="medium",
    ),
    "waste_organic_landfill": CarbonMapping(
        activity_type="waste_organic_landfill",
        label="Waste: organic landfill",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": "waste-type_mixed_food_and_organic_garden-disposal_method_landfill",
            "source": "BEIS",
            "region": "GB",
            "year": 2019,
        },
        assumptions=(
            "Organic landfill uses the mixed food and garden waste landfill proxy published by BEIS.",
        ),
        confidence="medium",
    ),
    "waste_mixed_landfill": CarbonMapping(
        activity_type="waste_mixed_landfill",
        label="Waste: mixed landfill",
        category="waste",
        scope="personal",
        parameter_kind="weight",
        allowed_units=("kg",),
        selector={
            "activity_id": (
                "waste_management-type_municipal_solid_waste_"
                "treatment_of_municipal_solid_waste_open_dump_"
                "very_wet_infiltration_class_1000mm-disposal_method_landfill"
            ),
            "source": "ecoinvent",
            "region": "GLOBAL",
            "year": 2006,
        },
        assumptions=(
            "Mixed waste uses a municipal solid waste landfill proxy from ecoinvent.",
        ),
        confidence="medium",
    ),
}

DIRECT_ACTIVITY_TYPES: tuple[str, ...] = tuple(ACTIVITY_MAPPINGS.keys())

PERSONAL_TRANSPORT_TO_ACTIVITY: dict[str, str] = {
    "car_petrol": "transport_car_petrol",
    "car_diesel": "transport_car_diesel",
    "bus": "public_bus",
    "train": "train",
}

PERSONAL_FOOD_TO_ACTIVITY: dict[str, str] = {
    "beef": "food_beef",
    "chicken": "food_chicken",
    "seafood": "food_seafood",
    "milk": "food_milk",
    "eggs": "food_eggs",
    "fruit": "food_fruit",
    "vegetables": "food_vegetables",
    "grains": "food_grains",
    "legumes": "food_legumes",
}

WASTE_ACTIVITY_MATRIX: dict[str, dict[str, str]] = {
    "plastic": {
        "recycled": "waste_plastic_recycled",
        "landfill": "waste_plastic_landfill",
    },
    "paper": {
        "recycled": "waste_paper_recycled",
        "landfill": "waste_paper_landfill",
    },
    "glass": {
        "recycled": "waste_glass_recycled",
    },
    "organic": {
        "composted": "waste_organic_composted",
        "landfill": "waste_organic_landfill",
    },
    "mixed": {
        "landfill": "waste_mixed_landfill",
    },
}


def get_mapping(activity_type: str) -> CarbonMapping:
    try:
        return ACTIVITY_MAPPINGS[activity_type]
    except KeyError as exc:
        raise KeyError(f"Unsupported carbon activity_type '{activity_type}'") from exc


def list_factor_metadata() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for mapping in ACTIVITY_MAPPINGS.values():
        rows.append(
            {
                "activity_type": mapping.activity_type,
                "label": mapping.label,
                "category": mapping.category,
                "scope": mapping.scope,
                "allowed_units": list(mapping.allowed_units),
                "parameter_kind": mapping.parameter_kind,
                "selector": dict(mapping.selector),
                "assumptions": list(mapping.assumptions),
                "confidence": mapping.confidence,
                "notes": list(mapping.notes),
            }
        )
    return rows


def get_supported_units(activity_type: str) -> tuple[str, ...]:
    return get_mapping(activity_type).allowed_units


def get_personal_activity_for_transport(mode: str) -> str:
    return PERSONAL_TRANSPORT_TO_ACTIVITY[mode]


def get_personal_activity_for_food(food_category: str) -> str:
    return PERSONAL_FOOD_TO_ACTIVITY[food_category]


def get_supported_waste_treatments(waste_type: str) -> tuple[str, ...]:
    return tuple(WASTE_ACTIVITY_MATRIX.get(waste_type, {}).keys())


def get_personal_activity_for_waste(waste_type: str, treatment: str) -> str:
    return WASTE_ACTIVITY_MATRIX[waste_type][treatment]
