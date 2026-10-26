from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Annotated
import app.models
from router.auth import verify_token
from app.database import engine, SessionLocal, Base
from sqlalchemy.orm import Session

movies = APIRouter(tags = ["Movies"])

Base.metadata.create_all(bind = engine)

class Movie(BaseModel):
    id : int
    title : str
    duration : int
    rating : float = Field(gt = 0, le = 5)

class UpdateMovie(BaseModel):
    title : str
    duration : int
    rating : float = Field(gt = 0, le = 5)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
authenticate = Annotated[dict,Depends(verify_token)]


@movies.post("/movie")
async def add_movie(new_movie : Movie, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    movies = app.models.Movie(**new_movie.model_dump())
    db.add(movies)
    db.commit()
    db.refresh(movies)
    return movies

@movies.get("/movie")
async def get_movie(db : db_dependency):
    movies = db.query(app.models.Movie).all()
    return movies

@movies.get("/movies/{movie_id}")
async def single_movie(movie_id : int, db : db_dependency):
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code = 404, detail = 'Movie not found')
    return movie

@movies.put("/movies/{movie_id}")
async def update_movie(movie_id : int, update_movie : UpdateMovie, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code = 404, detail = 'Movie not found')
    movie.title = update_movie.title
    movie.duration = update_movie.duration
    movie.rating = update_movie.rating
    db.commit()
    return update_movie

@movies.delete("/movies/{movie_id}")
async def remove_movie(movie_id : int, db : db_dependency, user : authenticate):
    if user is None:
        raise HTTPException(status_code = 404, detail = 'Authentication failed')
    movie = db.query(app.models.Movie).filter(app.models.Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code = 404, detail = 'Movie not found')
    db.delete(movie)
    db.commit()
    return movie