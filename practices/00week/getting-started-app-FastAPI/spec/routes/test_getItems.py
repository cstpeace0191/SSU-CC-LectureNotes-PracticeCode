from unittest.mock import AsyncMock, patch
import pytest
from src.routes.items import get_items

ITEMS = [{"id": "12345", "name": "Item 1", "completed": False}]


@pytest.mark.asyncio
async def test_it_gets_items_correctly():
    with patch("src.routes.items.db.get_items", new_callable=AsyncMock) as mock_get_items:
        mock_get_items.return_value = ITEMS

        res = await get_items()

        assert mock_get_items.call_count == 1
        assert len(res) == 1
        assert res[0]["id"] == ITEMS[0]["id"]
        assert res[0]["name"] == ITEMS[0]["name"]
        assert res[0]["completed"] == ITEMS[0]["completed"]
