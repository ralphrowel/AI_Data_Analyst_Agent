"""FastAPI API routes for Data Quality, Profiling, Cleaning, and Lineage capabilities."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.auth.rate_limiter import RateLimit
from backend.app.auth.supabase_auth import get_current_user, User
from backend.app.data_quality.plan import CleaningPlanRequest
from backend.app.data_quality.service import default_dq_service
from backend.app.paths import filename as validate_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["data-quality"])


@router.get("/{name}/profile")
def get_dataset_profile(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Generates and returns comprehensive structural and statistical profile of a dataset."""
    try:
        safe_name = validate_filename(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset name",
        )

    try:
        profile = default_dq_service.profile_dataset(safe_name, user_id=current_user.id)
        return profile.to_dict()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to profile dataset '%s': %s", name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dataset profile",
        )


@router.get(
    "/{name}/quality",
    dependencies=[Depends(RateLimit(limit=30, window_seconds=60, name="quality assessment"))],
)
def get_dataset_quality(
    name: str,
    refresh: bool = Query(False, description="Force recompute bypassing cached report"),
    current_user: User = Depends(get_current_user),
):
    """Generates and returns comprehensive data quality assessment, issue inventory, and score."""
    try:
        safe_name = validate_filename(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset name",
        )

    try:
        assessment = default_dq_service.assess_dataset(
            safe_name, user_id=current_user.id, force_refresh=refresh
        )
        return assessment.to_dict()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to assess quality for dataset '%s': %s", name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quality assessment",
        )


@router.post(
    "/{name}/clean/preview",
    dependencies=[Depends(RateLimit(limit=20, window_seconds=60, name="cleaning preview"))],
)
def preview_cleaning(
    name: str,
    plan: CleaningPlanRequest,
    current_user: User = Depends(get_current_user),
):
    """Dry-runs a data cleaning plan returning before/after stats and audit diff without saving."""
    try:
        safe_name = validate_filename(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset name",
        )

    try:
        preview = default_dq_service.preview_cleaning(
            safe_name, plan=plan.to_engine_options(), user_id=current_user.id
        )
        return preview
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to preview cleaning for dataset '%s': %s", name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cleaning preview",
        )


@router.post(
    "/{name}/clean",
    dependencies=[Depends(RateLimit(limit=10, window_seconds=60, name="dataset cleaning"))],
)
def apply_cleaning(
    name: str,
    plan: CleaningPlanRequest,
    current_user: User = Depends(get_current_user),
):
    """Executes a cleaning plan, saves derived clean dataset, and records audit & lineage."""
    try:
        safe_name = validate_filename(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset name",
        )

    try:
        job = default_dq_service.apply_cleaning(
            safe_name, plan=plan.to_engine_options(), user_id=current_user.id
        )
        return job.to_dict()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to clean dataset '%s': %s", name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean dataset",
        )


@router.get(
    "/{name}/lineage",
    dependencies=[Depends(RateLimit(limit=60, window_seconds=60, name="lineage query"))],
)
def get_dataset_lineage(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieves lineage, derivation hierarchy, and cleaning job history for a dataset."""
    try:
        safe_name = validate_filename(name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dataset name",
        )

    try:
        lineage = default_dq_service.get_dataset_lineage(safe_name, user_id=current_user.id)
        return lineage.to_dict()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{name}' not found",
        )
    except Exception as e:
        logger.exception("Failed to load lineage for dataset '%s': %s", name, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dataset lineage",
        )
