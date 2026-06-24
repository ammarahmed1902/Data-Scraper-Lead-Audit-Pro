"""Tests for reports API list endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_reports_returns_200(client: AsyncClient):
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reports-list-test@example.com",
            "password": "securepass123",
            "full_name": "Reports Test",
        },
    )
    if register.status_code == 409:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "reports-list-test@example.com",
                "password": "securepass123",
            },
        )
        token = login.json()["tokens"]["access_token"]
    else:
        register.raise_for_status()
        token = register.json()["tokens"]["access_token"]

    response = await client.get(
        "/api/v1/reports?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
