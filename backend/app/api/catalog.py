"""Catalog metadata router — filter options, models, providers."""

from fastapi import APIRouter

from ..core import enums
from ..llm import discover_models, provider_options
from ..schemas.api import CatalogOut

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog() -> CatalogOut:
    return CatalogOut(
        business_functions=enums.BUSINESS_FUNCTIONS,
        tasks=enums.TASKS,
        applications=enums.APPLICATIONS,
        statuses=enums.PROMPT_STATUSES,
        classifications=enums.DATA_CLASSIFICATIONS,
        risk_levels=enums.RISK_LEVELS,
        input_types=enums.INPUT_TYPES,
        audiences=enums.AUDIENCES,
        tones=enums.TONES,
        output_formats=enums.OUTPUT_FORMATS,
        event_types=enums.EVENT_TYPES,
        roles=enums.ROLES,
        models=discover_models(),
        providers=provider_options(),
    )
