CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token TEXT
);

CREATE TABLE chat_requests (
    id SERIAL PRIMARY KEY,
    sender_id INT REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INT REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    CONSTRAINT unique_friendship UNIQUE (sender_id, receiver_id)
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_id INT REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INT REFERENCES users(id) ON DELETE CASCADE,
    encrypted_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
