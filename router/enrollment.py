from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
import app.models
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field


enroll = APIRouter(tags = ["Enroll"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Enroll(BaseModel):
    name : str
    roll_number : str = Field(max_length=10)


db_dependency = Annotated[Session, Depends(get_db)]

@enroll.post("/enrollments/{event_id}")
async def enroll_event(event_id : int, enroll : Enroll, db : db_dependency):
    event = db.query(app.models.Events).filter(app.models.Events.id == event_id).first()
    if event is None:
        raise HTTPException(status_code = 404, detail = 'No events found')
    current_time = datetime.now()
    if current_time > event.deadline:
        raise HTTPException(status_code = 409, detail = 'Registration has been closed')
    relation = db.query(app.models.Register, app.models.EventManager).join(app.models.EventManager, app.models.Register.id == app.models.EventManager.student_id).filter(app.models.Register.roll_number == enroll.roll_number, app.models.EventManager.event_id == event_id).first()
    if relation:
        raise HTTPException(status_code = 409, detail = 'The user can register for the event once!')
    new_student = app.models.Register(**enroll.model_dump())
    try:
        db.add(new_student)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code = 409, detail = 'Duplicate enrollment or Unusual activivty detected')
    student = app.models.EventManager(
        event_id = event_id,
        name = new_student.name,
        student_id = new_student.id,
        roll_number = new_student.roll_number
    )
    try:
        db.add(student)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code = 409, detail = 'Database constraint violation')from exc
    except Exception:
        db.rollback()
        raise
    return {"message" : "Registered for the event successfully"}