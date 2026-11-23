from unittest.mock import AsyncMock, patch
import pytest
from src.routes.items import delete_item


@pytest.mark.asyncio
async def test_it_removes_item_correctly():
    item_id = "12345"

    with patch("src.routes.items.db.remove_item", new_callable=AsyncMock) as mock_remove:
        res = await delete_item(item_id)

        assert mock_remove.call_count == 1
        mock_remove.assert_awaited_once_with(item_id)
        assert res == {"status": "ok"}
