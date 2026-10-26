from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from router.auth import verify_token
import app.models
from app.database import SessionLocal


event = APIRouter(tags = ["Event"])



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Event(BaseModel):
    event_name : str
    deadline : datetime
    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, value: datetime):
        if value.tzinfo is not None and value.utcoffset() is not None:
            raise ValueError("Deadline must use local college time without a timezone offset")
        return value




db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict, Depends(verify_token)]



@event.post("/events")
async def new_event(event : Event, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 403, detail = 'Unauthorized Access')
    current_time = datetime.now()
    event_deadline = event.deadline
    if current_time > event_deadline:
        raise HTTPException(status_code = 400, detail = 'Registration has been closed!')
    new_event = app.models.Events(
        event_name = event.event_name,
        deadline = event.deadline
    )
    try:
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
    except Exception as exc:
        db.rollback()
        print(f"error while creating event {exc}")
        raise HTTPException(status_code = 500, detail = 'Check the backend terminal')
    return {"message" : "Added event successfully", "event_id" : new_event.id, "event_name" : new_event.event_name, "deadline" : new_event.deadline}


@event.get("/events")
async def get_events(db: db_dependency):
    try:
        events = db.query(app.models.Events).all()
        return events
    except Exception:
        db.rollback()
        raise HTTPException(status_code = 404, detail = 'No events found')


@event.delete("/events/{event_id}")
async def remove_event(event_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Unauthorized Access')
    events = db.query(app.models.Events).filter(app.models.Events.id == event_id).first()
    if events is None:
        raise HTTPException(status_code = 404, detail = 'No events found')
    db.query(app.models.EventManager).filter(app.models.EventManager.event_id == event_id).delete()
    try:
        db.delete(events)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message" : "Event has been removed successfully"}




@event.get("/events/{event_id}")
async def event_relation(event_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Unauthorized access')
    try:
        event = db.query(app.models.Events).filter(app.models.Events.id == event_id).first()
        if event is None:
            raise HTTPException(status_code = 404, detail = 'No event found')
        students = db.query(app.models.Register).join(app.models.EventManager, app.models.Register.id == app.models.EventManager.student_id).filter(app.models.EventManager.event_id == event_id).all()
        if not students:
            raise HTTPException(status_code = 404, detail = 'No student found')
        return students
    except HTTPException:
        raise
    except Exception as exc:
        print(f"error retrieving event registrations: {exc}")
        raise HTTPException(status_code = 500, detail = 'Failed to retrieve the records') from exc 
