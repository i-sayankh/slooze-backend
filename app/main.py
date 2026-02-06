from fastapi import FastAPI
from app.routers import auth
from app.routers import restaurants
from app.routers import menu_items
from app.routers import orders
from app.routers import payments

app = FastAPI()

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(menu_items.router)
app.include_router(orders.router)
app.include_router(payments.router)
