"""Website management business logic."""

import json
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.website import Website, WebsiteStatus
from app.repositories.website_repository import WebsiteRepository
from app.schemas.common import PaginatedResponse
from app.schemas.website import (
    WebsiteBulkCreate,
    WebsiteBulkResult,
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteResponse,
    WebsiteUpdate,
)
from app.utils.helpers import extract_domain, is_valid_url, normalize_url


def _tags_to_list(tags: str | None) -> list[str] | None:
    if not tags:
        return None
    try:
        parsed = json.loads(tags)
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None


def _tags_to_str(tags: list[str] | None) -> str | None:
    if not tags:
        return None
    return json.dumps(tags)


def _to_response(website: Website) -> WebsiteResponse:
    data = {
        "id": website.id,
        "owner_id": website.owner_id,
        "url": website.url,
        "domain": website.domain,
        "company_name": website.company_name,
        "contact_name": website.contact_name,
        "contact_email": website.contact_email,
        "contact_phone": website.contact_phone,
        "industry": website.industry,
        "status": website.status,
        "notes": website.notes,
        "tags": _tags_to_list(website.tags),
        "last_audited_at": website.last_audited_at,
        "created_at": website.created_at,
        "updated_at": website.updated_at,
    }
    return WebsiteResponse.model_validate(data)


class WebsiteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WebsiteRepository(session)

    async def list_websites(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[WebsiteListResponse]:
        skip = (page - 1) * page_size
        websites = await self.repo.get_by_owner(
            owner_id=owner_id,
            skip=skip,
            limit=page_size,
            status=status,
            search=search,
        )
        total = await self.repo.count_by_owner(
            owner_id=owner_id, status=status, search=search
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[WebsiteListResponse.model_validate(w) for w in websites],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_website(self, website_id: uuid.UUID, owner_id: uuid.UUID) -> WebsiteResponse:
        website = await self.repo.get_by_id_for_owner(website_id, owner_id)
        if website is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
        return _to_response(website)

    async def create_website(
        self, data: WebsiteCreate, owner_id: uuid.UUID
    ) -> WebsiteResponse:
        normalized = normalize_url(data.url)
        if not is_valid_url(normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid website URL format",
            )

        domain = extract_domain(normalized)
        existing = await self.repo.get_by_domain(domain, owner_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Website with domain '{domain}' already exists",
            )

        website = Website(
            owner_id=owner_id,
            url=normalized,
            domain=domain,
            company_name=data.company_name,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            industry=data.industry,
            notes=data.notes,
            tags=_tags_to_str(data.tags),
            status=WebsiteStatus.PENDING.value,
        )
        website = await self.repo.create(website)
        return _to_response(website)

    async def update_website(
        self,
        website_id: uuid.UUID,
        data: WebsiteUpdate,
        owner_id: uuid.UUID,
    ) -> WebsiteResponse:
        website = await self.repo.get_by_id_for_owner(website_id, owner_id)
        if website is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")

        if data.url is not None:
            normalized = normalize_url(data.url)
            if not is_valid_url(normalized):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid website URL format",
                )
            domain = extract_domain(normalized)
            existing = await self.repo.get_by_domain(domain, owner_id)
            if existing and existing.id != website.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Website with domain '{domain}' already exists",
                )
            website.url = normalized
            website.domain = domain

        if data.company_name is not None:
            website.company_name = data.company_name
        if data.contact_name is not None:
            website.contact_name = data.contact_name
        if data.contact_email is not None:
            website.contact_email = data.contact_email
        if data.contact_phone is not None:
            website.contact_phone = data.contact_phone
        if data.industry is not None:
            website.industry = data.industry
        if data.status is not None:
            website.status = data.status.value
        if data.notes is not None:
            website.notes = data.notes
        if data.tags is not None:
            website.tags = _tags_to_str(data.tags)

        website = await self.repo.update(website)
        return _to_response(website)

    async def delete_website(self, website_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        website = await self.repo.get_by_id_for_owner(website_id, owner_id)
        if website is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")
        await self.repo.delete(website)

    async def bulk_create(
        self, data: WebsiteBulkCreate, owner_id: uuid.UUID
    ) -> WebsiteBulkResult:
        created = 0
        skipped = 0
        errors: list[dict[str, str]] = []
        seen_domains: set[str] = set()

        for index, item in enumerate(data.websites):
            try:
                normalized = normalize_url(item.url)
                if not is_valid_url(normalized):
                    errors.append({"index": str(index), "url": item.url, "error": "Invalid URL"})
                    continue

                domain = extract_domain(normalized)
                if domain in seen_domains:
                    skipped += 1
                    continue

                existing = await self.repo.get_by_domain(domain, owner_id)
                if existing:
                    skipped += 1
                    seen_domains.add(domain)
                    continue

                website = Website(
                    owner_id=owner_id,
                    url=normalized,
                    domain=domain,
                    company_name=item.company_name,
                    contact_name=item.contact_name,
                    contact_email=item.contact_email,
                    contact_phone=item.contact_phone,
                    industry=item.industry,
                    notes=item.notes,
                    tags=_tags_to_str(item.tags),
                    status=WebsiteStatus.PENDING.value,
                )
                await self.repo.create(website)
                seen_domains.add(domain)
                created += 1
            except Exception as exc:
                errors.append({"index": str(index), "url": item.url, "error": str(exc)})

        return WebsiteBulkResult(created=created, skipped=skipped, errors=errors)
