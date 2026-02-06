from fastapi import FastAPI
from app.routers import auth
from app.routers import restaurants
from app.routers import menu_items

app = FastAPI()

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(menu_items.router)
