from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.carbon.calculators import haversine_km, pairwise, round_kg
from app.carbon.climatiq_client import ClimatiqClient
from app.carbon.mappings import (
    CarbonMapping,
    get_mapping,
    get_personal_activity_for_food,
    get_personal_activity_for_transport,
    get_personal_activity_for_waste,
    list_factor_metadata,
)
from app.carbon.personal_habits import (
    PersonalHabitTemplate,
    get_personal_habit_template,
    list_personal_habit_templates,
)
from app.core.config import settings
from app.models.truck_state import TruckStateVersion
from app.repositories.truck_repository import TruckRepository
from app.schemas.carbon import (
    CalculationStatus,
    CarbonBatchEvaluationOut,
    CarbonBatchEvaluationRequest,
    CarbonEvaluationOut,
    CarbonEvaluationRequest,
    CarbonFactorsOut,
    CarbonTruckDerivedOut,
    CarbonTruckHistoryOut,
    CarbonTruckSegmentOut,
    FootprintScope,
    PersonalCategoryTotalsOut,
    PersonalDailyFootprintOut,
    PersonalDailyFootprintRequest,
    PersonalHabitCatalogOut,
    PersonalEvaluatedItemOut,
)
from app.schemas.truck import TruckStateOut


@dataclass
class PendingEvaluation:
    activity_type: str
    quantity: float
    unit: str
    timestamp: datetime
    mapping: CarbonMapping
    request_body: dict[str, Any]
    assumptions: list[str]
    confidence: str
    method: str
    allocation_divisor: int | None = None


@dataclass
class PendingPersonalItem:
    category: str
    label: str
    source_type: str
    source_key: str
    pending: PendingEvaluation


class CarbonService:
    def __init__(self, db: Session | None = None, client: ClimatiqClient | None = None) -> None:
        self.db = db
        self.client = client or ClimatiqClient()
        self.repo = TruckRepository(db) if db is not None else None

    def evaluate(self, payload: CarbonEvaluationRequest) -> CarbonEvaluationOut:
        pending = self._build_pending_evaluation(
            activity_type=payload.activity_type.value,
            quantity=payload.quantity,
            unit=payload.unit,
            timestamp=payload.timestamp,
            method="climatiq_basic_estimate",
        )
        response = self.client.estimate(pending.request_body)
        return self._build_output_from_provider(pending, response)

    def evaluate_batch(self, payload: CarbonBatchEvaluationRequest) -> CarbonBatchEvaluationOut:
        pending_items = [
            self._build_pending_evaluation(
                activity_type=item.activity_type.value,
                quantity=item.quantity,
                unit=item.unit,
                timestamp=item.timestamp,
                method="climatiq_basic_estimate",
            )
            for item in payload.evaluations
        ]
        responses = self.client.estimate_batch([item.request_body for item in pending_items])
        results = [
            self._build_output_from_provider(pending, response)
            for pending, response in zip(pending_items, responses, strict=True)
        ]
        return CarbonBatchEvaluationOut(
            accepted=len(results),
            total_co2e_kg=round_kg(sum(item.co2e_kg for item in results)),
            results=results,
        )

    def get_factor_catalog(self) -> CarbonFactorsOut:
        return CarbonFactorsOut(
            provider="climatiq",
            data_version=settings.CLIMATIQ_DATA_VERSION,
            factors=list_factor_metadata(),
        )

    def get_personal_habit_catalog(self) -> PersonalHabitCatalogOut:
        return PersonalHabitCatalogOut(habits=list_personal_habit_templates())

    def evaluate_personal_daily(
        self, payload: PersonalDailyFootprintRequest
    ) -> PersonalDailyFootprintOut:
        evaluation_timestamp = datetime.combine(
            payload.date, time.min, tzinfo=timezone.utc
        )
        items: list[PendingPersonalItem] = []

        for entry in payload.transport:
            activity_type = get_personal_activity_for_transport(entry.mode.value)
            assumptions: list[str] = []
            allocation_divisor: int | None = None
            if entry.occupancy is not None:
                allocation_divisor = entry.occupancy
                assumptions.append(
                    f"Vehicle emissions are allocated equally across occupancy={entry.occupancy}."
                )
            items.append(
                PendingPersonalItem(
                    category="transport",
                    label=entry.mode.value,
                    source_type="entry",
                    source_key=entry.mode.value,
                    pending=self._build_pending_evaluation(
                        activity_type=activity_type,
                        quantity=entry.distance_km,
                        unit="km" if "car_" in entry.mode.value else "passenger_km",
                        timestamp=evaluation_timestamp,
                        assumptions=assumptions,
                        method="climatiq_basic_estimate_personal_daily",
                        allocation_divisor=allocation_divisor,
                    ),
                )
            )

        for entry in payload.food:
            activity_type = get_personal_activity_for_food(entry.food_category.value)
            items.append(
                PendingPersonalItem(
                    category="food",
                    label=entry.food_category.value,
                    source_type="entry",
                    source_key=entry.food_category.value,
                    pending=self._build_pending_evaluation(
                        activity_type=activity_type,
                        quantity=entry.quantity,
                        unit=entry.unit,
                        timestamp=evaluation_timestamp,
                        method="climatiq_basic_estimate_personal_daily",
                    ),
                )
            )

        for entry in payload.utilities:
            items.append(
                PendingPersonalItem(
                    category="utilities",
                    label=entry.activity_type.value,
                    source_type="entry",
                    source_key=entry.activity_type.value,
                    pending=self._build_pending_evaluation(
                        activity_type=entry.activity_type.value,
                        quantity=entry.quantity,
                        unit=entry.unit,
                        timestamp=evaluation_timestamp,
                        method="climatiq_basic_estimate_personal_daily",
                    ),
                )
            )

        for entry in payload.waste:
            activity_type = get_personal_activity_for_waste(
                entry.waste_type.value, entry.treatment
            )
            items.append(
                PendingPersonalItem(
                    category="waste",
                    label=f"{entry.waste_type.value}:{entry.treatment}",
                    source_type="entry",
                    source_key=f"{entry.waste_type.value}:{entry.treatment}",
                    pending=self._build_pending_evaluation(
                        activity_type=activity_type,
                        quantity=entry.quantity,
                        unit=entry.unit,
                        timestamp=evaluation_timestamp,
                        method="climatiq_basic_estimate_personal_daily",
                    ),
                )
            )

        for entry in payload.habits:
            template = get_personal_habit_template(entry.habit_type)
            items.extend(
                self._expand_habit_entry(
                    template=template,
                    count=entry.count,
                    timestamp=evaluation_timestamp,
                )
            )

        responses = self.client.estimate_batch([item.pending.request_body for item in items])
        evaluated_items: list[PersonalEvaluatedItemOut] = []
        category_totals = PersonalCategoryTotalsOut()

        for item, response in zip(items, responses, strict=True):
            evaluation = self._build_output_from_provider(item.pending, response)
            evaluated_items.append(
                PersonalEvaluatedItemOut(
                    category=item.category,
                    label=item.label,
                    source_type=item.source_type,
                    source_key=item.source_key,
                    evaluation=evaluation,
                )
            )
            current = getattr(category_totals, item.category)
            setattr(category_totals, item.category, round_kg(current + evaluation.co2e_kg))

        total = round_kg(
            category_totals.transport
            + category_totals.food
            + category_totals.utilities
            + category_totals.waste
        )
        return PersonalDailyFootprintOut(
            scope=FootprintScope.personal,
            person_id=payload.person_id,
            date=payload.date,
            total_co2e_kg=total,
            category_totals=category_totals,
            items=evaluated_items,
        )

    def _expand_habit_entry(
        self,
        template: PersonalHabitTemplate,
        count: float,
        timestamp: datetime,
    ) -> list[PendingPersonalItem]:
        expanded: list[PendingPersonalItem] = []
        for component in template.components:
            mapping = get_mapping(component.activity_type)
            assumptions = list(template.assumptions) + list(component.assumptions)
            assumptions.append(
                f"The reported habit count is multiplied by the fixed per-occurrence template quantity for '{template.habit_type}'."
            )
            expanded.append(
                PendingPersonalItem(
                    category=template.category,
                    label=f"{template.habit_type}:{component.label}",
                    source_type="habit",
                    source_key=template.habit_type,
                    pending=self._build_pending_evaluation(
                        activity_type=component.activity_type,
                        quantity=count * component.quantity_per_occurrence,
                        unit=component.unit,
                        timestamp=timestamp,
                        assumptions=assumptions,
                        confidence=mapping.confidence,
                        method="climatiq_basic_estimate_personal_habit_template",
                    ),
                )
            )
        return expanded

    def derive_latest_truck_footprint(self, truck_id: str) -> CarbonTruckDerivedOut | None:
        repo = self._require_repo()
        latest = repo.get_latest(truck_id)
        if latest is None:
            return None

        history = self._get_truck_history_oldest_first(truck_id)
        if len(history) < 2:
            return CarbonTruckDerivedOut(
                truck_id=truck_id,
                status=CalculationStatus.needs_clarification,
                latest_truck_state=self._truck_state_to_out(latest),
                total_distance_km=0.0,
                segment_count=0,
                from_version=latest.version,
                to_version=latest.version,
                evaluation=self._build_needs_clarification_output(
                    activity_type="waste_collection_truck",
                    quantity=0.0,
                    unit="km",
                    timestamp=latest.position_timestamp,
                    assumptions=[
                        "At least two stored truck positions are required to derive distance.",
                    ],
                    method="deterministic_needs_clarification",
                ),
            )

        total_distance_km = round_kg(sum(self._segment_distance_km(a, b) for a, b in pairwise(history)))
        pending = self._build_pending_evaluation(
            activity_type="waste_collection_truck",
            quantity=total_distance_km,
            unit="km",
            timestamp=latest.position_timestamp,
            assumptions=[
                "The cumulative truck footprint is derived from consecutive GPS points with the Haversine formula.",
            ],
            confidence="medium",
            method="climatiq_basic_estimate_haversine_derived",
        )
        response = self.client.estimate(pending.request_body)
        evaluation = self._build_output_from_provider(pending, response)
        return CarbonTruckDerivedOut(
            scope=FootprintScope.fleet,
            truck_id=truck_id,
            status=evaluation.status,
            latest_truck_state=self._truck_state_to_out(latest),
            total_distance_km=total_distance_km,
            segment_count=max(len(history) - 1, 0),
            from_version=history[0].version,
            to_version=history[-1].version,
            evaluation=evaluation,
        )

    def derive_truck_history(
        self, truck_id: str, page: int = 1, page_size: int = 50
    ) -> CarbonTruckHistoryOut | None:
        repo = self._require_repo()
        latest = repo.get_latest(truck_id)
        if latest is None:
            return None

        history = self._get_truck_history_oldest_first(truck_id)
        if len(history) < 2:
            return CarbonTruckHistoryOut(
                scope=FootprintScope.fleet,
                truck_id=truck_id,
                total=0,
                page=page,
                page_size=page_size,
                total_distance_km=0.0,
                total_co2e_kg=0.0,
                records=[],
            )

        segments = list(pairwise(history))
        pending_items: list[tuple[TruckStateVersion, TruckStateVersion, float, PendingEvaluation]] = []
        for previous, current in segments:
            distance_km = self._segment_distance_km(previous, current)
            pending_items.append(
                (
                    previous,
                    current,
                    distance_km,
                    self._build_pending_evaluation(
                        activity_type="waste_collection_truck",
                        quantity=distance_km,
                        unit="km",
                        timestamp=current.position_timestamp,
                        assumptions=[
                            "Truck segment emissions are derived from straight-line GPS distance.",
                        ],
                        confidence="medium",
                        method="climatiq_basic_estimate_haversine_segment",
                    ),
                )
            )

        responses = self.client.estimate_batch(
            [item[3].request_body for item in pending_items]
        )
        evaluated_segments: list[CarbonTruckSegmentOut] = []
        total_distance_km = 0.0
        total_co2e_kg = 0.0

        for (previous, current, distance_km, pending), response in zip(
            pending_items, responses, strict=True
        ):
            evaluation = self._build_output_from_provider(pending, response)
            total_distance_km += distance_km
            total_co2e_kg += evaluation.co2e_kg
            evaluated_segments.append(
                CarbonTruckSegmentOut(
                    scope=FootprintScope.fleet,
                    truck_id=current.truck_id,
                    from_version=previous.version,
                    to_version=current.version,
                    distance_km=round_kg(distance_km),
                    from_position_timestamp=previous.position_timestamp,
                    to_position_timestamp=current.position_timestamp,
                    waste_type=current.waste_type.value,
                    evaluation=evaluation,
                )
            )

        evaluated_segments.reverse()
        skip = (page - 1) * page_size
        paged_records = evaluated_segments[skip : skip + page_size]

        return CarbonTruckHistoryOut(
            scope=FootprintScope.fleet,
            truck_id=truck_id,
            total=len(evaluated_segments),
            page=page,
            page_size=page_size,
            total_distance_km=round_kg(total_distance_km),
            total_co2e_kg=round_kg(total_co2e_kg),
            records=paged_records,
        )

    def _build_pending_evaluation(
        self,
        activity_type: str,
        quantity: float,
        unit: str,
        timestamp: datetime | None,
        method: str,
        assumptions: list[str] | None = None,
        confidence: str | None = None,
        allocation_divisor: int | None = None,
    ) -> PendingEvaluation:
        mapping = get_mapping(activity_type)
        normalized_timestamp = self._normalize_timestamp(timestamp)
        params = self._build_parameters(mapping, quantity, unit)
        selector = dict(mapping.selector)
        selector["data_version"] = settings.CLIMATIQ_DATA_VERSION
        request_body = {
            "emission_factor": selector,
            "parameters": params,
        }
        return PendingEvaluation(
            activity_type=activity_type,
            quantity=quantity,
            unit=unit,
            timestamp=normalized_timestamp,
            mapping=mapping,
            request_body=request_body,
            assumptions=list(assumptions or []),
            confidence=confidence or mapping.confidence,
            method=method,
            allocation_divisor=allocation_divisor,
        )

    def _build_parameters(
        self, mapping: CarbonMapping, quantity: float, unit: str
    ) -> dict[str, Any]:
        if mapping.parameter_kind == "distance":
            return {"distance": quantity, "distance_unit": unit}
        if mapping.parameter_kind == "energy":
            return {"energy": quantity, "energy_unit": unit}
        if mapping.parameter_kind == "volume":
            return {"volume": quantity, "volume_unit": unit}
        if mapping.parameter_kind == "weight":
            return {"weight": quantity, "weight_unit": unit}
        if mapping.parameter_kind == "passenger_over_distance":
            return {"passengers": 1, "distance": quantity, "distance_unit": "km"}
        raise RuntimeError(f"Unsupported parameter kind '{mapping.parameter_kind}'")

    def _build_output_from_provider(
        self, pending: PendingEvaluation, response: dict[str, Any]
    ) -> CarbonEvaluationOut:
        emission_factor_meta = response.get("emission_factor") or {}
        activity_data = response.get("activity_data") or {}
        activity_value = float(activity_data.get("activity_value") or pending.quantity)
        activity_unit = activity_data.get("activity_unit")
        co2e_kg = float(response.get("co2e") or 0.0)
        emission_factor = (
            co2e_kg / activity_value if activity_value > 0 else None
        )
        factor_unit = f"kgCO2e/{activity_unit}" if activity_unit else None

        assumptions = list(pending.mapping.assumptions) + list(pending.assumptions)
        if pending.allocation_divisor and pending.allocation_divisor > 1:
            co2e_kg = co2e_kg / pending.allocation_divisor
            if emission_factor is not None:
                emission_factor = emission_factor / pending.allocation_divisor
            factor_unit = "kgCO2e/km_per_person_share"

        source_name = emission_factor_meta.get("source")
        source = f"climatiq:{source_name}" if source_name else "climatiq"
        provider_activity_id = emission_factor_meta.get("activity_id") or pending.mapping.selector.get(
            "activity_id"
        )
        provider_factor_id = emission_factor_meta.get("id")
        provider_data_version = emission_factor_meta.get("data_version") or settings.CLIMATIQ_DATA_VERSION

        return CarbonEvaluationOut(
            scope=pending.mapping.scope,
            co2e_kg=round_kg(co2e_kg),
            unit="kgCO2e",
            source=source,
            method=pending.method,
            activity_type=pending.activity_type,
            emission_factor=round_kg(emission_factor) if emission_factor is not None else None,
            factor_unit=factor_unit,
            assumptions=list(dict.fromkeys(assumptions)),
            confidence=pending.confidence,
            status=CalculationStatus.ok,
            timestamp=pending.timestamp,
            input_quantity=pending.quantity,
            input_unit=pending.unit,
            provider_factor_id=provider_factor_id,
            provider_activity_id=str(provider_activity_id) if provider_activity_id is not None else None,
            provider_data_version=str(provider_data_version) if provider_data_version is not None else None,
        )

    def _build_needs_clarification_output(
        self,
        activity_type: str,
        quantity: float,
        unit: str,
        timestamp: datetime | None,
        assumptions: list[str],
        method: str,
    ) -> CarbonEvaluationOut:
        mapping = get_mapping(activity_type)
        return CarbonEvaluationOut(
            scope=mapping.scope,
            co2e_kg=0.0,
            unit="kgCO2e",
            source=f"climatiq:{mapping.selector.get('source')}",
            method=method,
            activity_type=activity_type,
            emission_factor=None,
            factor_unit=None,
            assumptions=list(dict.fromkeys(list(mapping.assumptions) + assumptions)),
            confidence=mapping.confidence,
            status=CalculationStatus.needs_clarification,
            timestamp=self._normalize_timestamp(timestamp),
            input_quantity=quantity,
            input_unit=unit,
            provider_factor_id=None,
            provider_activity_id=str(mapping.selector.get("activity_id")),
            provider_data_version=settings.CLIMATIQ_DATA_VERSION,
        )

    def _truck_state_to_out(self, state: TruckStateVersion) -> TruckStateOut:
        return TruckStateOut(
            id=state.id,
            truck_id=state.truck_id,
            company_id=state.company_id,
            waste_type=state.waste_type.value,
            latitude=state.latitude,
            longitude=state.longitude,
            position_timestamp=state.position_timestamp,
            version=state.version,
            created_at=state.created_at,
        )

    def _get_truck_history_oldest_first(self, truck_id: str) -> list[TruckStateVersion]:
        repo = self._require_repo()
        total = repo.count_by_truck(truck_id)
        return list(reversed(repo.get_history(truck_id, skip=0, limit=total)))

    def _segment_distance_km(
        self, previous: TruckStateVersion, current: TruckStateVersion
    ) -> float:
        return haversine_km(
            previous.latitude,
            previous.longitude,
            current.latitude,
            current.longitude,
        )

    def _normalize_timestamp(self, value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _require_repo(self) -> TruckRepository:
        if self.repo is None:
            raise RuntimeError("A database session is required for truck-derived carbon operations")
        return self.repo
