from unittest.mock import AsyncMock, patch
import pytest
from src.models import ItemCreate
from src.routes.items import add_item


@pytest.mark.asyncio
async def test_it_stores_item_correctly():
    fake_id = "something-not-a-uuid"
    name = "A sample item"
    payload = ItemCreate(name=name)

    with patch("src.routes.items.uuid.uuid4", return_value=fake_id), \
         patch("src.routes.items.db.store_item", new_callable=AsyncMock) as mock_store:

        expected_item = {
            "id": fake_id,
            "name": name,
            "completed": False,
        }

        res = await add_item(payload)

        assert mock_store.call_count == 1
        mock_store.assert_awaited_once_with(expected_item)
        assert res["id"] == expected_item["id"]
        assert res["name"] == expected_item["name"]
        assert res["completed"] == expected_item["completed"]
