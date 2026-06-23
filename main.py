from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
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

# --- LOGIN ENDPOINT ---
@app.post("/login", response_model=schemas.Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.email == form_data.username) | (models.User.username == form_data.username)
    ).first()

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token, "token_type": "bearer"}

# --- CRUD: CREATE A TASK ---
@app.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # UPDATED: Changed .dict() to .model_dump()
    new_task = models.Task(**task.model_dump(), user_id=current_user.user_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# --- CRUD: READ ALL TASKS FOR THE LOGGED-IN USER ---
@app.get("/tasks", response_model=list[schemas.TaskResponse])
def get_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.user_id == current_user.user_id).all()
    return tasks

# --- CRUD: UPDATE AN EXISTING TASK ---
@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.task_id == task_id, models.Task.user_id == current_user.user_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
        
    # UPDATED: Changed .dict(exclude_unset=True) to .model_dump(exclude_unset=True)
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    db.commit()
    db.refresh(db_task)
    return db_task

# --- CRUD: DELETE A TASK ---
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.task_id == task_id, models.Task.user_id == current_user.user_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")
        
    db.delete(db_task)
    db.commit()
    return None

