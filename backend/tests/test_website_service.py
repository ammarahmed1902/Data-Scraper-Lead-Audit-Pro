"""Website service unit tests."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.models.website import Website, WebsiteStatus
from app.schemas.website import WebsiteBulkCreate, WebsiteCreate, WebsiteUpdate
from app.services.website_service import WebsiteService


def _make_website(
    owner_id: uuid.UUID | None = None,
    url: str = "https://example.com",
    domain: str = "example.com",
) -> Website:
    return Website(
        id=uuid.uuid4(),
        owner_id=owner_id or uuid.uuid4(),
        url=url,
        domain=domain,
        status=WebsiteStatus.PENDING.value,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return WebsiteService(mock_session)


async def _persist_website(website: Website) -> Website:
    website.id = uuid.uuid4()
    website.created_at = datetime.now(UTC)
    website.updated_at = datetime.now(UTC)
    return website


@pytest.mark.asyncio
async def test_create_website_success(service):
    owner_id = uuid.uuid4()
    service.repo = MagicMock()
    service.repo.get_by_domain = AsyncMock(return_value=None)
    service.repo.create = AsyncMock(side_effect=_persist_website)

    data = WebsiteCreate(url="example.com", company_name="Acme")
    result = await service.create_website(data, owner_id)

    assert result.url == "https://example.com"
    assert result.domain == "example.com"
    assert result.company_name == "Acme"
    assert result.status == WebsiteStatus.PENDING


@pytest.mark.asyncio
async def test_create_website_duplicate_domain(service):
    owner_id = uuid.uuid4()
    service.repo = MagicMock()
    service.repo.get_by_domain = AsyncMock(return_value=_make_website(owner_id))

    with pytest.raises(HTTPException) as exc:
        await service.create_website(WebsiteCreate(url="https://example.com"), owner_id)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_website_invalid_url(service):
    owner_id = uuid.uuid4()
    service.repo = MagicMock()

    with pytest.raises(HTTPException) as exc:
        await service.create_website(WebsiteCreate.model_construct(url="not-a-url"), owner_id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_website_not_found(service):
    service.repo = MagicMock()
    service.repo.get_by_id_for_owner = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.get_website(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_website_success(service):
    owner_id = uuid.uuid4()
    website = _make_website(owner_id)
    service.repo = MagicMock()
    service.repo.get_by_id_for_owner = AsyncMock(return_value=website)
    service.repo.get_by_domain = AsyncMock(return_value=None)
    service.repo.update = AsyncMock(side_effect=lambda w: w)

    data = WebsiteUpdate(company_name="Updated Corp", status=WebsiteStatus.COMPLETED)
    result = await service.update_website(website.id, data, owner_id)

    assert result.company_name == "Updated Corp"
    assert result.status == WebsiteStatus.COMPLETED


@pytest.mark.asyncio
async def test_delete_website_success(service):
    owner_id = uuid.uuid4()
    website = _make_website(owner_id)
    service.repo = MagicMock()
    service.repo.get_by_id_for_owner = AsyncMock(return_value=website)
    service.repo.delete = AsyncMock()

    await service.delete_website(website.id, owner_id)
    service.repo.delete.assert_called_once_with(website)


@pytest.mark.asyncio
async def test_list_websites_pagination(service):
    owner_id = uuid.uuid4()
    websites = [_make_website(owner_id) for _ in range(2)]
    service.repo = MagicMock()
    service.repo.get_by_owner = AsyncMock(return_value=websites)
    service.repo.count_by_owner = AsyncMock(return_value=25)

    result = await service.list_websites(owner_id, page=1, page_size=20)

    assert len(result.items) == 2
    assert result.total == 25
    assert result.total_pages == 2


@pytest.mark.asyncio
async def test_bulk_create_dedup_and_errors(service):
    owner_id = uuid.uuid4()
    service.repo = MagicMock()
    service.repo.get_by_domain = AsyncMock(return_value=None)
    service.repo.create = AsyncMock(side_effect=_persist_website)

    data = WebsiteBulkCreate(
        websites=[
            WebsiteCreate(url="https://a.com"),
            WebsiteCreate(url="https://a.com"),
            WebsiteCreate.model_construct(url="not-valid"),
            WebsiteCreate(url="https://b.com"),
        ]
    )
    result = await service.bulk_create(data, owner_id)

    assert result.created == 2
    assert result.skipped == 1
    assert len(result.errors) == 1
