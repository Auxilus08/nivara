from app.schemas.privacy import PrivacySettings, PrivacySettingsPatch

_settings = PrivacySettings()


def get_privacy_settings() -> PrivacySettings:
    return _settings.model_copy()


def update_privacy_settings(patch: PrivacySettingsPatch) -> PrivacySettings:
    global _settings
    _settings = _settings.model_copy(update=patch.model_dump(exclude_none=True))
    return get_privacy_settings()
