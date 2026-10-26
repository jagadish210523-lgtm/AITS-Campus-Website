from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
import app.models
from pwdlib import PasswordHash
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

auth = APIRouter(tags = ["Authentication"])


load_dotenv()
hash_password = PasswordHash.recommended()
oauth_security = OAuth2PasswordBearer(tokenUrl = "/login")
form = Annotated[OAuth2PasswordRequestForm, Depends()]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
TOKEN_EXPIRE_MINUTES = 30


class RegisterCredentials(BaseModel):
    username : str
    email : str
    password : str

db_dependency = Annotated[Session, Depends(get_db)]




@auth.post("/login")
async def login(db : db_dependency, user : form):
    username = user.username
    plain_password = user.password
    admin = db.query(app.models.User).filter(app.models.User.username == username).first()
    if admin is None:
        raise HTTPException(status_code = 401, detail = 'Invalid user or password')
    now = datetime.now(timezone.utc)
    hashed_password = hash_password.verify(plain_password,admin.password)
    if hashed_password is False:
        raise HTTPException(status_code = 401, detail = 'Incorrect password or user')
    if admin.role!="admin":
        raise HTTPException(status_code = 403, detail = "Admin access required")
    payload = {
        "sub" : str(admin.id),
        "role" : "admin",
        "iat" : now,
        "exp" : now + timedelta(minutes = TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm = "HS256")
    return {"access_token" : token, "token_type" : "bearer"}


def verify_token(user = Depends(oauth_security)):
    try:
        payload = jwt.decode(user, JWT_SECRET_KEY, algorithms = ["HS256"])
    except ExpiredSignatureError:
        raise HTTPException(status_code = 401, detail = 'Token Expired')
    except InvalidTokenError:
        raise HTTPException(status_code = 401, detail = 'Invalid Token')
    if payload.get("role") != "admin":
        raise HTTPException(status_code = 403, detail = 'Admin access required')
    return payload



authenticate = Annotated[dict, Depends(verify_token)]



@auth.post("/register")
async def registration(new_user : RegisterCredentials, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Unauthorized access')
    existing_user = db.query(app.models.User).filter(app.models.User.username == new_user.username).first()
    if existing_user:
        raise HTTPException(status_code = 403, detail = 'User already exists')
    user_record = app.models.User(
        username = new_user.username,
        email = new_user.email,
        role = "admin",
        password = hash_password.hash(new_user.password)
    )
    db.add(user_record)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message" : "User registered successfully"}