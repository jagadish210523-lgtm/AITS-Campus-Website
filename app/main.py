from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import router.events
import router.auth
import router.enrollment
from app.database import Base, engine


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://aits-campus-website-frontend.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind = engine)

app.include_router(router.events.event)
app.include_router(router.auth.auth)
app.include_router(router.enrollment.enroll)