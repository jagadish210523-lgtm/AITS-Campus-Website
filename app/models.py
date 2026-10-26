from sqlalchemy import Integer,Column,String,Float, ForeignKey, DateTime,UniqueConstraint
from app.database import Base


class Events(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key = True)
    event_name = Column(String(100))
    deadline = Column(DateTime)

class Register(Base):
    __tablename__ = "registration"
    id = Column(Integer, primary_key = True)
    name = Column(String(100), nullable = False)
    roll_number = Column(String(10), nullable = False)
    team_member = Column(String(100), nullable = True)

class User(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key = True)
    username = Column(String(70), unique = True)
    email = Column(String(100))
    password = Column(String(255))
    role = Column(String(15))

class EventManager(Base):
    __tablename__ = "event_manager"
    __table_args__ = (UniqueConstraint("event_id","roll_number",name = "uq_event_student"),)
    id = Column(Integer, primary_key = True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String(75))
    roll_number = Column(String(10), nullable = False)
    student_id = Column(Integer, ForeignKey("registration.id"))
