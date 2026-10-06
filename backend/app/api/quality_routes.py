"""FastAPI API routes for Data Quality and Profiling capabilities."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.auth.supabase_auth import get_current_user, User
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
