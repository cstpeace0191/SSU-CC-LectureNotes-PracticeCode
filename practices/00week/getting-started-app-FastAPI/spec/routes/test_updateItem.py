from unittest.mock import AsyncMock, patch
import pytest
from src.models import ItemUpdate
from src.routes.items import update_item

ITEM = {
    "id": "1234",
    "name": "New title",
    "completed": False,
}


@pytest.mark.asyncio
async def test_it_updates_items_correctly():
    item_id = "1234"
    payload = ItemUpdate(name="New title", completed=False)

    with patch("src.routes.items.db.update_item", new_callable=AsyncMock) as mock_update, \
         patch("src.routes.items.db.get_item", new_callable=AsyncMock) as mock_get:

        mock_get.return_value = ITEM

        res = await update_item(item_id, payload)

        assert mock_update.call_count == 1
        mock_update.assert_awaited_once_with(
            item_id,
            {"name": "New title", "completed": False},
        )

        assert mock_get.call_count == 1
        mock_get.assert_awaited_once_with(item_id)

        assert res["id"] == ITEM["id"]
        assert res["name"] == ITEM["name"]
        assert res["completed"] == ITEM["completed"]
