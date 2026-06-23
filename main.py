from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db, engine
import models
import schemas
import auth

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

# --- REGISTRATION ENDPOINT ---
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if the email already exists in the database
    db_email = db.query(models.User).filter(models.User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # 2. Check if the username already exists
    db_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # 3. Hash the raw password
    hashed_pwd = auth.hash_password(user.password)

    # 4. Create the new User object using the database model
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd
    )

    # 5. Save the user to MySQL
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Refreshes object to include the auto-generated user_id and created_at

    return new_user
