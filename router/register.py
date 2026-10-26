from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from router.auth import verify_token
from app.database import engine, Base, SessionLocal
import app.models
from sqlalchemy.orm import Session


register = APIRouter(tags = ["Register"])



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict, Depends(verify_token)]



class Registration(BaseModel):
    name : str
    roll_number : str


@register.post("/event")
async def new_records(student : Registration, db : db_dependency):
    new_student = app.models.Register(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


@register.get("/event")
async def get_records(db : db_dependency):
    records = db.query(app.models.Register).all()
    if not records:
        raise HTTPException(status_code = 404, detail = 'No records found')
    return records


@register.put("/event/{record_id}")
async def update_record(record_id : int, db : db_dependency, update_student : Registration):
    record = db.query(app.models.Register).filter(app.models.Register.id == record_id).first()
    if record is None:
        raise HTTPException(status_code = 404, detail = 'No records found')
    record.name = update_student.name
    record.roll_number = update_student.roll_number
    db.commit()
    return update_student


@register.delete("/event/{record_id}")
async def remove_student(record_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Unauthorized Access')
    student = db.query(app.models.Register).filter(app.models.Register.id == record_id).first()
    if student is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    db.delete(student)
    db.commit()
    return student