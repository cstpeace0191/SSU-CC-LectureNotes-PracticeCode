import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from src.models import Item, ItemCreate, ItemUpdate
from src.persistence import db

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=List[Item])
async def get_items():
    items = await db.get_items()
    return items


@router.post("", response_model=Item, status_code=status.HTTP_200_OK)
async def add_item(payload: ItemCreate):
    item = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "completed": False,
    }
    await db.store_item(item)
    return item


@router.put("/{item_id}", response_model=Item)
async def update_item(item_id: str, payload: ItemUpdate):
    await db.update_item(
        item_id,
        {
            "name": payload.name,
            "completed": payload.completed,
        },
    )
    item = await db.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item(item_id: str):
    await db.remove_item(item_id)
    return {"status": "ok"}
