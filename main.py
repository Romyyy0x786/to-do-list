import os
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt

# --- CONFIGURATION ---
SECRET_KEY = "supersecretkey"  # Change this for production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MONGO_URL = "mongodb+srv://sohail:hugfug@cluster0.dy2k1ve.mongodb.net/?appName=Cluster0" # Ensure MongoDB is running
DB_NAME = "todo_app_db"

# --- APP SETUP ---
app = FastAPI()

# Enable CORS for React [cite: 10]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE ---
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# --- SECURITY UTILS ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- PYDANTIC MODELS ---
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BoardCreate(BaseModel):
    title: str

class BoardOut(BaseModel):
    id: str = Field(alias="_id")
    title: str
    owner_id: str

class TodoCreate(BaseModel):
    content: str
    status: str = "pending" # pending, in-progress, done

class TodoUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None

class TodoOut(BaseModel):
    id: str = Field(alias="_id")
    content: str
    status: str
    board_id: str

# --- DEPENDENCIES ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ROUTES ---
@app.post("/register", status_code=201)
async def register(user: UserCreate):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = {"email": user.email, "hashed_password": hashed_password}
    await db.users.insert_one(new_user)
    return {"message": "User created successfully"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- BOARD ROUTES ---
@app.post("/boards", response_model=BoardOut)
async def create_board(board: BoardCreate, current_user: dict = Depends(get_current_user)):
    new_board = {
        "title": board.title,
        "owner_id": str(current_user["_id"])
    }
    result = await db.boards.insert_one(new_board)
    created_board = await db.boards.find_one({"_id": result.inserted_id})
    # Helper to convert ObjectId to str for response
    created_board["_id"] = str(created_board["_id"])
    return created_board

@app.get("/boards", response_model=List[BoardOut])
async def get_boards(current_user: dict = Depends(get_current_user)):
    boards = []
    cursor = db.boards.find({"owner_id": str(current_user["_id"])})
    async for board in cursor:
        board["_id"] = str(board["_id"])
        boards.append(board)
    return boards

@app.delete("/boards/{board_id}")
async def delete_board(board_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.boards.delete_one({"_id": ObjectId(board_id), "owner_id": str(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Board not found")
    # Also delete todos associated with this board
    await db.todos.delete_many({"board_id": board_id})
    return {"message": "Board deleted"}

# --- TODO ROUTES ---
@app.post("/boards/{board_id}/todos", response_model=TodoOut)
async def create_todo(board_id: str, todo: TodoCreate, current_user: dict = Depends(get_current_user)):
    # Verify board ownership first
    board = await db.boards.find_one({"_id": ObjectId(board_id), "owner_id": str(current_user["_id"])})
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    new_todo = {
        "content": todo.content,
        "status": todo.status,
        "board_id": board_id
    }
    result = await db.todos.insert_one(new_todo)
    created_todo = await db.todos.find_one({"_id": result.inserted_id})
    created_todo["_id"] = str(created_todo["_id"])
    return created_todo

@app.get("/boards/{board_id}/todos", response_model=List[TodoOut])
async def get_todos(board_id: str, current_user: dict = Depends(get_current_user)):
    # Verify board ownership
    board = await db.boards.find_one({"_id": ObjectId(board_id), "owner_id": str(current_user["_id"])})
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
        
    todos = []
    cursor = db.todos.find({"board_id": board_id})
    async for todo in cursor:
        todo["_id"] = str(todo["_id"])
        todos.append(todo)
    return todos

@app.put("/todos/{todo_id}", response_model=TodoOut)
async def update_todo(todo_id: str, todo_update: TodoUpdate, current_user: dict = Depends(get_current_user)):
    # Need to verify if the todo belongs to a board owned by user
    # This is a bit complex in NoSQL without joins, 
    # but for simplicity we fetch the todo, then the board.
    todo = await db.todos.find_one({"_id": ObjectId(todo_id)})
    if not todo:
         raise HTTPException(status_code=404, detail="Todo not found")
    
    board = await db.boards.find_one({"_id": ObjectId(todo["board_id"]), "owner_id": str(current_user["_id"])})
    if not board:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = {k: v for k, v in todo_update.dict().items() if v is not None}
    
    if update_data:
        await db.todos.update_one({"_id": ObjectId(todo_id)}, {"$set": update_data})
    
    updated_todo = await db.todos.find_one({"_id": ObjectId(todo_id)})
    updated_todo["_id"] = str(updated_todo["_id"])
    return updated_todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str, current_user: dict = Depends(get_current_user)):
    todo = await db.todos.find_one({"_id": ObjectId(todo_id)})
    if not todo:
         raise HTTPException(status_code=404, detail="Todo not found")
    
    board = await db.boards.find_one({"_id": ObjectId(todo["board_id"]), "owner_id": str(current_user["_id"])})
    if not board:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.todos.delete_one({"_id": ObjectId(todo_id)})
    return {"message": "Todo deleted"}