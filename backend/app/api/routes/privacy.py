from fastapi import APIRouter

from app.schemas.privacy import PrivacySettings, PrivacySettingsPatch
from app.services.privacy import get_privacy_settings, update_privacy_settings

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


@router.get("/settings", response_model=PrivacySettings)
async def read_privacy_settings() -> PrivacySettings:
    return get_privacy_settings()


@router.patch("/settings", response_model=PrivacySettings)
async def patch_privacy_settings(request: PrivacySettingsPatch) -> PrivacySettings:
    return update_privacy_settings(request)
