from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.routers import restaurants
from app.routers import menu_items
from app.routers import orders
from app.routers import payments

allow_origins = [
    "https://slooze-frontend-theta.vercel.app",
    "http://localhost:3000",
]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(menu_items.router)
app.include_router(orders.router)
app.include_router(payments.router)
