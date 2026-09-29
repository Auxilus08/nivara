import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.trusted_contact import TrustedContactMethod


class TrustedContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    contact_method: TrustedContactMethod
    contact_value: str = Field(min_length=1, max_length=320)

    @field_validator("name", "contact_value")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @model_validator(mode="after")
    def validate_contact_value(self):
        if self.contact_method is TrustedContactMethod.EMAIL:
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.contact_value):
                raise ValueError("contact_value must be a valid email address")
        elif self.contact_method is TrustedContactMethod.PHONE:
            if not re.fullmatch(r"[0-9+().\-\s]{7,32}", self.contact_value) or not re.search(r"\d", self.contact_value):
                raise ValueError("contact_value must be a valid phone value")
        return self


class TrustedContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    contact_method: TrustedContactMethod | None = None
    contact_value: str | None = Field(default=None, min_length=1, max_length=320)

    @field_validator("name", "contact_value", mode="before")
    @classmethod
    def trim_required_text_and_reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("value must not be null")
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("contact_method", mode="before")
    @classmethod
    def reject_null_contact_method(cls, value: TrustedContactMethod | None) -> TrustedContactMethod:
        if value is None:
            raise ValueError("contact_method must not be null")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("at least one contact field is required")
        return self


class TrustedContactResponse(BaseModel):
    id: UUID
    name: str
    contact_method: TrustedContactMethod
    contact_value: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TrustedContactListResponse(BaseModel):
    contacts: list[TrustedContactResponse]
    count: int


class TrustedContactSharingPreferencePatch(BaseModel):
    allow_trip_status: bool | None = None
    allow_location: bool | None = None
    allow_emergency: bool | None = None

    @field_validator("allow_trip_status", "allow_location", "allow_emergency", mode="before")
    @classmethod
    def reject_null_permission(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("sharing permissions must not be null")
        return value

    @model_validator(mode="after")
    def require_at_least_one_permission(self):
        if not self.model_fields_set:
            raise ValueError("at least one sharing preference is required")
        return self


class TrustedContactSharingPreferenceResponse(BaseModel):
    trusted_contact_id: UUID
    allow_trip_status: bool
    allow_location: bool
    allow_emergency: bool
    created_at: datetime
    updated_at: datetime


class SafeTripTrustedContactCreate(BaseModel):
    trusted_contact_id: UUID


class SafeTripTrustedContactResponse(BaseModel):
    safe_trip_id: UUID
    trusted_contact_id: UUID
    created_at: datetime
    contact: TrustedContactResponse


class SafeTripTrustedContactListResponse(BaseModel):
    contacts: list[SafeTripTrustedContactResponse]
    count: int
