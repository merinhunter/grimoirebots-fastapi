from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import Annotated
from uuid import UUID
import datetime

from fastapi import FastAPI, Body, Path, Query, status, HTTPException


class Order(BaseModel):
    id: UUID
    title: str
    pub_date: datetime.datetime


class Projects(BaseModel):
    git: list[str]
    order: Order


class Setup(BaseModel):
    order: Order


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str

    class Config:
        schema_extra = {
            "example": {
                "url": "https://github.com/grimoirebots",
                "name": "Grimoirebots",
            }
        }


class Item(BaseModel):
    name: str
    description: str | None = Field(
        default=None, title="The description of the item", max_length=300
    )
    price: float = Field(
        ge=0, description="The price must be greater than zero"
    )
    tax: float | None = None
    tags: set[str] = set()
    images: list[Image] | None = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            }
        }


class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item]


class User(BaseModel):
    username: str
    full_name: str | None = None


class Tags(Enum):
    items = "items"
    users = "users"


app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights

@app.post("/offers/")
async def create_offer(offer: Offer):
    return offer

@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images

@app.get("/items/", tags=[Tags.items])
async def read_items(
    q: Annotated[
        str | None,
        Query(
            title="Query string",
            description="Query string for the items to search in the database that have a good match",
            min_length=3,
            alias="item-query",
            deprecated=True,
        ),
    ] = None
) -> list[Item]:
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]

@app.get("/items/{item_id}", tags=[Tags.items])
async def read_item(
    item_id: Annotated[str, Path(title="The ID of the item to get")],
):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}

@app.post(
    "/items/",
    status_code=status.HTTP_201_CREATED,
    tags=[Tags.items],
    response_description="The created item",
)
async def create_item(item: Item) -> Item:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict

@app.put("/items/{item_id}", tags=[Tags.items])
async def update_item(
    item_id: UUID,
    item: Annotated[
        Item,
        Body(
            examples={
                "normal": {
                    "summary": "A normal example",
                    "description": "A **normal** item works correctly.",
                    "value": {
                        "name": "Foo",
                        "description": "A very nice Item",
                        "price": 35.4,
                        "tax": 3.2,
                    },
                },
                "converted": {
                    "summary": "An example with converted data",
                    "description": "FastAPI can convert price `strings` to actual `numbers` automatically",
                    "value": {
                        "name": "Bar",
                        "price": "35.4",
                    },
                },
                "invalid": {
                    "summary": "Invalid data is rejected with an error",
                    "value": {
                        "name": "Baz",
                        "price": "thirty five point four",
                    },
                },
            },
        )
    ]
):
    return {
        "item_id": item_id,
        "item": item,
    }
