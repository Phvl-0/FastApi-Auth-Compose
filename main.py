import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Local module imports
from security import verify_password, hash_password
from database import engine, Base, get_db
from models import UserModel

# 1. LIFESPAN MANAGEMENT (Replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on server startup before handling requests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Runs on server shutdown (if needed)

# 2. APP & SECURITY CONFIGURATION
app = FastAPI(lifespan=lifespan)
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 3. REQUEST SCHEMAS
class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    id: str
    email: str
    password: str
    role: str = "voter"

# 4. TOKEN HELPER & AUTH DEPENDENCY
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_role: str = payload.get("role")
        email: str = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload"
            )
            
        return {"user_id": user_id, "role": user_role, "email": email}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 5. API ROUTES
@app.post("/register")
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists in PostgreSQL
    result = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create and save user record
    new_user = UserModel(
        id=user_data.id,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/login")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Query database for user by email
    result = await db.execute(select(UserModel).where(UserModel.email == credentials.email))
    user = result.scalars().first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )
    
    jwt_claims = {
        "sub": user.id,
        "role": user.role,
        "email": user.email
    }
    
    access_token = create_access_token(data=jwt_claims)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
def get_user_profile(current_user: dict = Depends(get_current_user)):
    return {"status": "authenticated", "profile": current_user}
