from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    get_trusted_contact_repository,
    get_trusted_contact_sharing_preference_repository,
)
from app.repositories.trusted_contact import (
    TrustedContactRepository,
    TrustedContactSharingPreferenceRepository,
)
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactListResponse,
    TrustedContactResponse,
    TrustedContactSharingPreferencePatch,
    TrustedContactSharingPreferenceResponse,
    TrustedContactUpdate,
)
from app.services.trusted_contacts import (
    TrustedContactNotFoundError,
    TrustedContactService,
    TrustedContactSharingPreferenceService,
)

router = APIRouter(prefix="/api/v1/trusted-contacts", tags=["trusted-contacts"])


@router.post("", response_model=TrustedContactResponse, status_code=status.HTTP_201_CREATED)
async def create_trusted_contact(
    request: TrustedContactCreate,
    repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
) -> TrustedContactResponse:
    return await TrustedContactService(repository).create(request)


@router.patch("/{contact_id}", response_model=TrustedContactResponse)
async def update_trusted_contact(
    contact_id: UUID,
    request: TrustedContactUpdate,
    repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
) -> TrustedContactResponse:
    try:
        return await TrustedContactService(repository).update(contact_id, request)
    except TrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=TrustedContactListResponse)
async def list_trusted_contacts(
    repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
) -> TrustedContactListResponse:
    return await TrustedContactService(repository).list()


@router.get("/{contact_id}", response_model=TrustedContactResponse)
async def get_trusted_contact(
    contact_id: UUID,
    repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
) -> TrustedContactResponse:
    try:
        return await TrustedContactService(repository).get(contact_id)
    except TrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trusted_contact(
    contact_id: UUID,
    repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
) -> Response:
    try:
        await TrustedContactService(repository).delete(contact_id)
    except TrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{contact_id}/sharing-preferences",
    response_model=TrustedContactSharingPreferenceResponse,
)
async def get_trusted_contact_sharing_preferences(
    contact_id: UUID,
    contact_repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
    preference_repository: TrustedContactSharingPreferenceRepository = Depends(
        get_trusted_contact_sharing_preference_repository
    ),
) -> TrustedContactSharingPreferenceResponse:
    try:
        return await TrustedContactSharingPreferenceService(
            contact_repository, preference_repository
        ).get(contact_id)
    except TrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{contact_id}/sharing-preferences",
    response_model=TrustedContactSharingPreferenceResponse,
)
async def update_trusted_contact_sharing_preferences(
    contact_id: UUID,
    request: TrustedContactSharingPreferencePatch,
    contact_repository: TrustedContactRepository = Depends(get_trusted_contact_repository),
    preference_repository: TrustedContactSharingPreferenceRepository = Depends(
        get_trusted_contact_sharing_preference_repository
    ),
) -> TrustedContactSharingPreferenceResponse:
    try:
        return await TrustedContactSharingPreferenceService(
            contact_repository, preference_repository
        ).update(contact_id, request)
    except TrustedContactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
