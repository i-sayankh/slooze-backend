from pydantic import BaseModel

from app.schemas.auth import CountryEnum


class RestaurantCreate(BaseModel):
    name: str
    country: CountryEnum


class RestaurantResponse(BaseModel):
    id: int
    name: str
    country: str

    class Config:
        from_attributes = True


class PaginationMetadata(BaseModel):
    total: int
    skip: int
    limit: int
    start: int  # 1-based index of first item on this page
    end: int  # 1-based index of last item on this page


class RestaurantListResponse(BaseModel):
    items: list[RestaurantResponse]
    pagination_metadata: PaginationMetadata


class RestaurantCreatedResponse(BaseModel):
    message: str
