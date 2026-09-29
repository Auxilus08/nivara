from pydantic import BaseModel


class PrivacySettings(BaseModel):
    location_sharing_enabled: bool = False
    trusted_contact_sharing_enabled: bool = False
    emergency_sharing_enabled: bool = False
    prototype_scope: str = "global_prototype_setting_not_user_isolated"


class PrivacySettingsPatch(BaseModel):
    location_sharing_enabled: bool | None = None
    trusted_contact_sharing_enabled: bool | None = None
    emergency_sharing_enabled: bool | None = None
