from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    name: str = Field(..., description="Name of the todo item")
    completed: bool = Field(False, description="Completion status")


class ItemCreate(BaseModel):
    name: str = Field(..., description="Name of the todo item")


class ItemUpdate(BaseModel):
    name: str = Field(..., description="Updated name of the todo item")
    completed: bool = Field(..., description="Updated completion status")


class Item(ItemBase):
    id: str = Field(..., description="Unique UUID identifier for the item")
