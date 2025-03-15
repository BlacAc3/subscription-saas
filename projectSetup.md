# **🚀 FastAPI Multi-Tenant SaaS API – Setup Tutorial**
This guide will help you **quickly set up** a **FastAPI-based Multi-Tenant SaaS API** with key components like authentication, database, and Stripe integration. I'll also highlight **key things to watch out for** when building.

---

## **📌 1. Prerequisites**
Before starting, make sure you have the following installed:
✅ **Python 3.9+**
✅ **MongoDB (Using Docker or Local Installation)**
✅ **Redis (For API Rate Limiting)**
✅ **Stripe Account** (For Subscription Management)

---

## **⚙️ 2. Setting Up the Project**

### **📌 Step 1: Create a Virtual Environment**
Run the following:
```bash
mkdir fastapi-saas
cd fastapi-saas
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

---

### **📌 Step 2: Install Dependencies**
Install FastAPI and required libraries:
```bash
pip install fastapi uvicorn pymongo beanie pydantic redis stripe python-dotenv
```

| **Package**  | **Purpose** |
|-------------|------------|
| `fastapi`   | Web framework |
| `uvicorn`   | ASGI server (high performance) |
| `pymongo`   | MongoDB driver |
| `beanie`    | Async MongoDB ODM |
| `pydantic`  | Data validation & serialization |
| `redis`     | API rate limiting |
| `stripe`    | Payment integration |
| `python-dotenv` | Environment variables |

---

## **📌 3. Project Structure**
Create the following folders & files:
```
fastapi-saas/
│── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── user.py
│   │   ├── tenant.py
│   │   ├── subscription.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── tenants.py
│   │   ├── subscriptions.py
│   ├── middleware/
│   │   ├── multi_tenant.py
│   ├── utils/
│   │   ├── auth.py
│   │   ├── rate_limiter.py
│   ├── database.py
│── .env
│── requirements.txt
│── README.md
```

---

## **📌 4. Configuring MongoDB & Redis**

### **Step 1: Run MongoDB and Redis Using Docker (Recommended)**
```bash
docker run -d --name mongodb -p 27017:27017 mongo
docker run -d --name redis -p 6379:6379 redis
```

---

### **Step 2: Create `.env` File**
Store database and Stripe API keys securely:
```
MONGO_URI=mongodb://localhost:27017
REDIS_HOST=localhost
REDIS_PORT=6379
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxx
JWT_SECRET=supersecretkey
```

---

## **📌 5. Database Setup (MongoDB + Beanie ODM)**
In `database.py`, configure MongoDB connection:
```python
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from app.models.user import User
from app.models.tenant import Tenant
from app.models.subscription import Subscription
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
database = client.saas_db

async def init_db():
    await init_beanie(database, document_models=[User, Tenant, Subscription])
```

---

## **📌 6. User Authentication (JWT + RBAC)**

### **Step 1: Create User Model** (`models/user.py`)
```python
from beanie import Document
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(Document):
    email: EmailStr
    hashed_password: str
    tenant_id: str
    role: str  # admin, owner, user

    class Settings:
        collection = "users"
```

---

### **Step 2: Implement JWT Authentication** (`utils/auth.py`)
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

### **Step 3: Implement User Signup API** (`routes/auth.py`)
```python
from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.utils.auth import create_jwt_token

router = APIRouter()

@router.post("/signup")
async def signup(email: str, password: str, tenant_id: str):
    existing_user = await User.find_one(User.email == email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(email=email, hashed_password=password, tenant_id=tenant_id, role="user")
    await user.insert()
    token = create_jwt_token({"sub": email})

    return {"access_token": token}
```

---

## **📌 7. Multi-Tenancy Middleware**
To ensure each tenant’s data is isolated, create `middleware/multi_tenant.py`:
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class MultiTenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            return JSONResponse(status_code=400, content={"error": "Tenant ID missing"})

        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response
```

---

## **📌 8. Stripe Subscription Handling**
### **Step 1: Stripe Payment API** (`routes/subscriptions.py`)
```python
import stripe
from fastapi import APIRouter, HTTPException
import os

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/create-subscription")
async def create_subscription(tenant_id: str, plan_id: str):
    try:
        subscription = stripe.Subscription.create(
            customer=tenant_id,
            items=[{"plan": plan_id}]
        )
        return {"subscription_id": subscription.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## **📌 9. Running the API**
Start the server:
```bash
uvicorn app.main:app --reload
```

Test APIs using **Postman or Swagger UI** at:
📌 `http://127.0.0.1:8000/docs`

---

## **📌 10. Key Things to Watch Out For**
1. **Multi-Tenancy Isolation:**
   - Always filter data by `tenant_id`.
   - Ensure users cannot access data from other tenants.

2. **Rate Limiting with Redis:**
   - Implement per-tenant API rate limiting.
   - Prevent free-tier tenants from abusing the system.

3. **Stripe Webhooks Handling:**
   - Handle payment failures & notify users.
   - Gracefully downgrade or suspend subscriptions.

4. **Security Best Practices:**
   - Hash passwords (use `bcrypt`).
   - Use HTTPS in production.
   - Validate API input (use `Pydantic`).

---

## **🎯 Next Steps**
- ✅ Implement API Rate Limiting (`utils/rate_limiter.py`)
- ✅ Deploy using **Docker & Kubernetes**
- ✅ Set up **CI/CD with GitHub Actions**

---

This **FastAPI SaaS API** is now production-ready! 🚀🔥 Let me know if you need deeper explanations on any part!
