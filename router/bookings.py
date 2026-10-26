from fastapi import APIRouter, Depends, HTTPException
import app.models
import router.theatres
from router.auth import verify_token
from app.database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Annotated

bookings = APIRouter(tags = ["Booking"])

Base.metadata.create_all(bind = engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TicketBooking(BaseModel):
    seat_id : int

db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict, Depends(verify_token)]



@bookings.get("/show/{show_id}/seats")
async def get_seats(show_id : int, db : db_dependency):
    show = db.query(app.models.Show).filter(app.models.Show.id == show_id).first()
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == show.Theatre_id).first()
    if theatre is None or show is None:
        raise HTTPException(status_code = 404, detail = 'No match found')


@bookings.post("/theatre/{theatre_id}/seats")
async def seat_arrangement(theatre_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    if theatre is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    seat = db.query(app.models.Seats).filter(app.models.Seats.theatre_id == theatre_id).all()
    if seat:
        raise HTTPException(status_code = 409, detail = 'seats are generated')
    for seat_number in range(1,theatre.total_seats + 1):
        seats = app.models.Seats(
            seat_number = seat_number, 
            theatre_id = theatre_id)
        db.add(seats)
    db.commit()


@bookings.get("/shows/{show_id}/seats")
async def get_seat(show_id : int, db : db_dependency):
    seat_status = []
    show = db.query(app.models.Show).filter(app.models.Show.id == show_id).first()
    if show is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == show.theatre_id).first()
    if theatre is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    seats = db.query(app.models.Seats).filter(app.models.Seats.theatre_id == theatre.id).all()
    bookings = db.query(app.models.Booking).filter(app.models.Booking.show_id == show.id).all()
    for seat in seats:
        is_booked = False
        for booking in bookings:
            if seat.id == booking.seat_id:
                is_booked = True
        seat_status.append({
            "seat" : seat.id,
            "availability" : "booked" if is_booked == True else "available"
        })
    return seat_status


@bookings.post("/shows/{show_id}/book")
async def booking(show_id : int,requested_seat : TicketBooking ,db : db_dependency):
    show = db.query(app.models.Show).filter(app.models.Show.id == show_id).first()
    if show is None:
        raise HTTPException(status_code = 404, detail = 'No shows found')
    seat = db.query(app.models.Seats).filter(app.models.Seats.id == requested_seat.seat_id).first()
    if seat is None:
        raise HTTPException(status_code = 404, detail = 'Seat is unavailable')
    if show.theatre_id != seat.theatre_id:
        raise HTTPException(status_code = 404, detail = 'No match found')
    booking = db.query(app.models.Booking).filter(app.models.Booking.show_id == show.id, app.models.Booking.seat_id == seat.id).first()
    if booking is not None:
        raise HTTPException(status_code = 409, detail = 'Already booked')

    booking_info = app.models.Booking(show_id = show.id,seat_id = seat.id)
    db.add(booking_info)
    db.commit()
    return "Booking successful"