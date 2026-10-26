from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM events"))
        print("Database connection successful!")
        print("Query executed successfully.")
except Exception as e:
    print("Database error:", repr(e))