from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
import models
from database import engine

# This line tells SQLAlchemy to create all tables defined in models.py if they don't exist yet
models.Base.metadata.create_all(bind=engine)


app = FastAPI(title="Task Manager API")

@app.get("/")
def read_root():
    return {"message": "Welcome to your Task Manager API!"}

# Temporary endpoint to test the MySQL connection
@app.get("/test-db")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Run a simple query to check if the database is responding
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Successfully connected to MySQL database!"}
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}
