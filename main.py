from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import secrets
from cryptography.fernet import Fernet
import random
import string

app = FastAPI(title="MaskChat Backend Server")

DB_URL = "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres"

SECRET_KEY = Fernet.generate_key()
cipher_suite = Fernet(SECRET_KEY)

def get_db():
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

class RegisterModel(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginModel(BaseModel):
    login_id: str  
    password: str

class RequestActionModel(BaseModel):
    request_id: int
    action: str  

class SendMessageModel(BaseModel):
    sender_id: int
    receiver_id: int
    text: str

def generate_random_mask(length: int) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(chars) for _ in range(length))

@app.post("/auth/register")
def register_user(user: RegisterModel, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (user.username, user.email))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username or Email already exists")
    
    hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    token = secrets.token_hex(20)
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, verification_token) VALUES (%s, %s, %s, %s) RETURNING id",
        (user.username, user.email, hashed_pw, token)
    )
    conn.commit()
    
    verification_link = f"http://127.0.0{token}"
    return {"message": "Registration successful. Please verify email.", "verification_link": verification_link}

@app.get("/auth/verify")
def verify_email(token: str, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE verification_token = %s", (token,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    cursor.execute("UPDATE users SET is_verified = TRUE, verification_token = NULL WHERE id = %s", (user['id'],))
    conn.commit()
    return {"message": "Email verified successfully! You can now login."}

@app.post("/auth/login")
def login_user(user: LoginModel, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (user.login_id, user.login_id))
    db_user = cursor.fetchone()
    
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    if not db_user['is_verified']:
        raise HTTPException(status_code=400, detail="Please verify your email first")
        
    return {"message": "Login successful", "user_id": db_user['id'], "username": db_user['username']}

@app.get("/users/search")
def search_user(username: str, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username = %s AND is_verified = TRUE", (username,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result

@app.post("/chat/request/send")
def send_chat_request(sender_id: int, receiver_id: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chat_requests (sender_id, receiver_id, status) VALUES (%s, %s, 'pending')", (sender_id, receiver_id))
        conn.commit()
    except:
        raise HTTPException(status_code=400, detail="Request already exists")
    return {"message": "Chat request sent"}

@app.post("/chat/request/action")
def handle_chat_request(action_data: RequestActionModel, conn=Depends(get_db)):
    cursor = conn.cursor()
    if action_data.action in ['accepted', 'ignored']:
        cursor.execute("UPDATE chat_requests SET status = %s WHERE id = %s", (action_data.action, action_data.request_id))
    elif action_data.action == 'deleted':
        cursor.execute("DELETE FROM chat_requests WHERE id = %s", (action_data.request_id,))
    conn.commit()
    return {"message": f"Request {action_data.action}"}

@app.post("/chat/message/send")
def send_message(msg: SendMessageModel, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status FROM chat_requests WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)",
        (msg.sender_id, msg.receiver_id, msg.receiver_id, msg.sender_id)
    )
    status_res = cursor.fetchone()
    if not status_res or status_res['status'] != 'accepted':
        raise HTTPException(status_code=403, detail="Chat not accepted yet")

    encrypted_text = cipher_suite.encrypt(msg.text.encode('utf-8')).decode('utf-8')
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, encrypted_text) VALUES (%s, %s, %s)", (msg.sender_id, msg.receiver_id, encrypted_text))
    conn.commit()
    return {"message": "Message sent"}

@app.get("/chat/messages/masked")
def get_masked_messages(user1: int, user2: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, sender_id, receiver_id, created_at FROM messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) ORDER BY created_at ASC",
        (user1, user2, user2, user1)
    )
    messages = cursor.fetchall()
    for msg in messages:
        msg['text'] = generate_random_mask(random.randint(5, 15))
    return messages

@app.post("/chat/messages/unlock")
def unlock_messages(user_id: int, password: str, user1: int, user2: int, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect Password")
        
    cursor.execute(
        "SELECT id, sender_id, receiver_id, encrypted_text, created_at FROM messages WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) ORDER BY created_at ASC",
        (user1, user2, user2, user1)
    )
    messages = cursor.fetchall()
    for msg in messages:
        decrypted_bytes = cipher_suite.decrypt(msg['encrypted_text'].encode('utf-8'))
        msg['text'] = decrypted_bytes.decode('utf-8')
        del msg['encrypted_text']
    return messages
