from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from app.database import SessionLocal, engine, Base
import app.models
from router.auth import verify_token
from datetime import date, time
from sqlalchemy.orm import Session

shows = APIRouter(tags = ["Shows"])

Base.metadata.create_all(bind = engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict, Depends(verify_token)]


class Timings(BaseModel):
    theatre_id : int
    movie_id : int
    show_date : date
    show_time : time


@shows.post("timing")
async def add_shows(new_show : Timings, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == new_show.theatre_id).first()
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == new_show.movie_id).first()
    if theatre is None or movie is None:
        raise HTTPException(status_code = 404, detail = 'No details found')
    show = db.query(app.models.TheatreMovie).filter(app.models.TheatreMovie.theatre_id == new_show.theatre_id, app.models.TheatreMovie.movie_id == new_show.movie_id).first()
    if show is None:
        raise HTTPException(status_code = 404, detail = 'No show found')
    show = app.models.Show(
        theatre_id = new_show.theatre_id,
        movie_id = new_show.movie_id,
        show_date = new_show.show_date,
        show_time = new_show.show_time
    )
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@shows.get("/movie/{movie_id}/shows")
async def movie_details(movie_id : int, db : db_dependency):
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code = 404, detail = 'No movie found')
    movie_info = db.query(app.models.Show).filter(app.models.Show.movie_id == movie_id).all()
    if not movie_info:
        raise HTTPException(status_code = 404, detail = 'No show found')
    return movie_info


@shows.get("/movie/{movie_id}/shows")
async def movie_details(movie_id : int, show_day : date, db : db_dependency):
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    movie_date = db.query(app.models.Show).filter(app.models.Show.show_date == show_day, app.models.Show.movie_id == movie_id).all()
    if not movie or not movie_date:
        raise HTTPException(status_code = 404, detail = 'No match found')
    return movie, movie_date

@shows.get("/theatre/{theatre_id}/shows")
async def theatre_details(theatre_id : int, show_day : date, db: db_dependency):
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    movie_date = db.query(app.models.Show).filter(app.models.Show.show_date == show_day, app.models.Show.theatre_id == theatre_id).all()
    if not theatre or not movie_date:
        raise HTTPException(status_code = 404, detail = 'No match found')
    return theatre, movie_date
