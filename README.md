# Slooze Backend

A RESTful backend API for a food ordering platform built with **FastAPI**, **SQLAlchemy** (async), and **PostgreSQL**. It supports user authentication with JWT, role-based access control (RBAC), restaurant and menu management, order workflows, and payment methods.

---

## Tech Stack

- **Framework:** FastAPI
- **Language:** Python 3.12+
- **Database:** PostgreSQL (async via `asyncpg`)
- **ORM:** SQLAlchemy 2.x (async)
- **Migrations:** Alembic
- **Auth:** JWT (via `python-jose`) + bcrypt password hashing
- **Validation:** Pydantic v2

---

## Project Structure

```
slooze-backend/
|-- alembic/                # Database migrations
|   |-- versions/           # Migration scripts
|   |-- env.py              # Alembic environment config
|-- app/
|   |-- core/
|   |   |-- config.py       # App settings (loaded from .env)
|   |   |-- dependencies.py # Shared FastAPI dependencies (DB session, current user)
|   |   |-- rbac.py         # Role-based access control helpers
|   |   |-- security.py     # Password hashing & JWT token utilities
|   |-- db/
|   |   |-- base.py         # SQLAlchemy declarative base
|   |   |-- session.py      # Async engine & session factory
|   |-- models/             # SQLAlchemy ORM models
|   |   |-- country.py
|   |   |-- menu_item.py
|   |   |-- order.py
|   |   |-- order_item.py
|   |   |-- payment_method.py
|   |   |-- restaurant.py
|   |   |-- role.py
|   |   |-- user.py
|   |-- routers/            # API route handlers
|   |   |-- auth.py         # Register & login
|   |   |-- menu_items.py   # CRUD for menu items
|   |   |-- orders.py       # Order lifecycle (create, add items, checkout, cancel)
|   |   |-- payments.py     # Payment method management
|   |   |-- restaurants.py  # Restaurant management
|   |-- schemas/            # Pydantic request/response models
|   |   |-- auth.py
|   |   |-- menu_item.py
|   |   |-- order.py
|   |   |-- payment.py
|   |   |-- restaurant.py
|   |-- main.py             # FastAPI app entry point
|   |-- seed.py             # Seed script for roles & countries
|-- alembic.ini             # Alembic configuration
|-- requirements.txt        # Python dependencies
|-- .gitignore
```

---

## Database Schema

The application uses the following PostgreSQL schema. Tables are linked by foreign keys as shown.

![Database schema](docs/database-schema.png)

| Table             | Purpose |
|-------------------|--------|
| `alembic_version` | Tracks applied migrations |
| `roles`           | User roles (ADMIN, MANAGER, MEMBER) |
| `countries`       | Countries (e.g. India, America) |
| `users`           | User accounts (role_id, country_id) |
| `restaurants`     | Restaurants (country_id) |
| `menu_items`      | Menu items per restaurant |
| `orders`          | Orders (user_id, restaurant_id, status, total_amount) |
| `order_items`     | Line items (order_id, menu_item_id, quantity, price) |
| `payment_methods` | User payment methods (user_id, type, provider, last_four, is_default) |

---

## Prerequisites

- **Python 3.12** or higher
- **PostgreSQL** (running locally or via a cloud provider)
- **pip** (Python package manager)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/slooze-backend.git
cd slooze-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/slooze
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

| Variable                     | Description                              | Default          |
| ---------------------------- | ---------------------------------------- | ---------------- |
| `DATABASE_URL`               | Async PostgreSQL connection string       | *(required)*     |
| `SECRET_KEY`                 | Secret used to sign JWT tokens           | `supersecretkey` |
| `ALGORITHM`                  | JWT signing algorithm                    | `HS256`          |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| Token expiry time in minutes             | `60`             |

> **Note:** The `DATABASE_URL` must use the `postgresql+asyncpg://` scheme for the async engine.

### 5. Create the PostgreSQL Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE slooze;
\q
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

This will create all the required tables: `roles`, `countries`, `users`, `restaurants`, `menu_items`, `orders`, `order_items`, and `payment_methods`.

### 7. Seed Roles and Countries

The application requires pre-seeded roles (`ADMIN`, `MANAGER`, `MEMBER`) and countries (`India`, `America`). Run the seed script:

```bash
python -m app.seed
```

### 8. Start the Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**.

---

## API Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints

### Auth

| Method | Endpoint         | Description              | Auth Required |
| ------ | ---------------- | ------------------------ | ------------- |
| POST   | `/auth/register` | Register a new user      | No            |
| POST   | `/auth/login`    | Login and get JWT token  | No            |

### Restaurants

| Method | Endpoint         | Description              | Roles Allowed           |
| ------ | ---------------- | ------------------------ | ----------------------- |
| POST   | `/restaurants/`  | Create a restaurant      | ADMIN                   |
| GET    | `/restaurants/`  | List restaurants         | ADMIN, MANAGER, MEMBER  |

### Menu Items

| Method | Endpoint                               | Description              | Roles Allowed           |
| ------ | -------------------------------------- | ------------------------ | ----------------------- |
| POST   | `/menu-items/`                         | Create a menu item       | ADMIN                   |
| GET    | `/menu-items/{restaurant_id}`          | List items by restaurant | ADMIN, MANAGER, MEMBER  |
| PATCH  | `/menu-items/{menu_item_id}/availability` | Toggle item availability | ADMIN                   |

### Orders

| Method | Endpoint                        | Description              | Roles Allowed           |
| ------ | ------------------------------- | ------------------------ | ----------------------- |
| GET    | `/orders/`                      | List orders              | ADMIN, MANAGER, MEMBER  |
| POST   | `/orders/`                      | Create a new order       | ADMIN, MANAGER, MEMBER  |
| POST   | `/orders/{order_id}/items`      | Add item to an order     | ADMIN, MANAGER, MEMBER  |
| POST   | `/orders/{order_id}/checkout`   | Checkout an order        | ADMIN, MANAGER          |
| PATCH  | `/orders/{order_id}/cancel`     | Cancel a placed order    | ADMIN, MANAGER          |

### Payment Methods

| Method | Endpoint                | Description              | Roles Allowed           |
| ------ | ----------------------- | ------------------------ | ----------------------- |
| POST   | `/payments/`            | Add a payment method     | ADMIN                   |
| GET    | `/payments/`            | List payment methods     | ADMIN, MANAGER, MEMBER  |
| PUT    | `/payments/{payment_id}`| Update a payment method  | ADMIN                   |

---

## Authentication

1. **Register** a user via `POST /auth/register` with name, email, password, role, and country.
2. **Login** via `POST /auth/login` to receive a JWT access token.
3. Include the token in subsequent requests using the `Authorization` header:
   ```
   Authorization: Bearer <your-access-token>
   ```

---

## Role-Based Access Control

The API enforces RBAC on all protected routes:

| Role      | Permissions                                                        |
| --------- | ------------------------------------------------------------------ |
| **ADMIN** | Full access to all resources across all countries                   |
| **MANAGER** | Access scoped to their own country; can checkout and cancel orders |
| **MEMBER** | Access scoped to their own country; can create orders and add items |

Non-admin users can only see restaurants, menu items, and orders belonging to their own country.

---

## Order Workflow

1. **Create** an order for a restaurant (`POST /orders/`).
2. **Add items** to the order (`POST /orders/{order_id}/items`).
3. **Checkout** the order with a payment method (`POST /orders/{order_id}/checkout`) ? status moves from `CREATED` to `PLACED`.
4. **Cancel** a placed order if needed (`PATCH /orders/{order_id}/cancel`) ? status moves to `CANCELLED`.

---

## CORS

The backend is configured to allow requests from the following origins:

- `http://localhost:3000`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:5173`

---

## Useful Commands

```bash
# Run the dev server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Seed roles and countries
python -m app.seed
```
