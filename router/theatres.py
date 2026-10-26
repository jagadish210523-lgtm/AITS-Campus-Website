from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated
import router.movies
import app.models
from router.auth import verify_token
from app.database import engine, SessionLocal, Base
from sqlalchemy.orm import Session

theatres = APIRouter(tags = ["Theatre"])

Base.metadata.create_all(bind = engine)

class Theatre(BaseModel):
    id : int
    theatre_name : str
    total_seats : int

class UpdatedTheatre(BaseModel):
    theatre_name : str
    total_seats : int

def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally :
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict, Depends(verify_token)]


@theatres.post("/theatre")
async def add_theatre(new_theatre : Theatre, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    new_theatre = app.models.Theatre(**new_theatre.model_dump())
    db.add(new_theatre)
    db.commit()
    db.refresh(new_theatre)
    return {"message" : "Added new theatre successfully"}


@theatres.get("/theatre")
async def movie_theatre(db : db_dependency):
    theatres = db.query(app.models.Theatre).all()
    return theatres


@theatres.get("/theatre/{theatre_id}")
async def single_theatre(theatre_id : int, db : db_dependency):
    theatres = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    if not theatres:
        raise HTTPException(status_code = 404, detail = 'Theatre not found')
    return theatres

@theatres.put("/theatre/{theatre_id}")
async def update_theatre(theatre_id : int, theatre_update : UpdatedTheatre, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    theatres = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    if theatres is None:
        raise HTTPException(status_code = 404, detail = 'No theatre found')
    theatres.theatre_name = theatre_update.theatre_name
    theatres.total_seats = theatre_update.total_seats
    db.commit()
    return theatre_update


@theatres.delete("/theatre/{theatre_id}")
async def remove_theatre(theatre_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    theatres = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    if theatres is None:
        raise HTTPException(status_code = 404, detail = 'No theatre found')
    db.delete(theatres)
    db.commit()
    return theatres

# Building a connection between the theatres and movies


@theatres.post("/theatre/{theatre_id}/movie/{movie_id}")
async def theatre_and_movie(theatre_id : int, movie_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if theatre is None or movie is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    theatres = app.models.TheatreMovie(
        theatre_id = theatre_id,
        movie_id = movie_id
    )
    db.add(theatres)
    db.commit()
    return {"message" : "Movie added to theatre successfully"}



@theatres.get("/theatre/{theatre_id}/movie")
async def get_relation(theatre_id : int, db : db_dependency):
    theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == theatre_id).first()
    if theatre is None:
        raise HTTPException(status_code = 404, detail = 'Theatre not found')
    theatres = db.query(app.models.TheatreMovie).filter(app.models.TheatreMovie.theatre_id == theatre_id).all()

    movies_list = []

    for relation in theatres:
        movie = db.query(app.models.Movie).filter(app.models.Movie.id == relation.movie_id).first()
        movies_list.append(movie)
    return movies_list



@theatres.get("/movie/{movie_id}/theatre")
async def get_theatre_movie(movie_id : int, db : db_dependency):
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code = 404, detail = 'No match found')
    movies = db.query(app.models.TheatreMovie).filter(app.models.TheatreMovie.movie_id == movie_id).all()

    theatres_list = []

    for relation in movies:
        theatre = db.query(app.models.Theatre).filter(app.models.Theatre.id == relation.theatre_id).first()
        theatres_list.append(theatre)
    return theatres_list
        