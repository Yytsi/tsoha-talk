CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

CREATE TABLE forums (
    id SERIAL PRIMARY KEY,
    name VARCHAR(40) UNIQUE NOT NULL,
    is_secret BOOLEAN DEFAULT FALSE,
    access_list TEXT[]
);

CREATE TABLE threads (
    id SERIAL PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    forum_id INTEGER REFERENCES forums(id) ON DELETE CASCADE,
    creator_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    thread_id INTEGER REFERENCES threads(id) ON DELETE CASCADE,
    posted_by INTEGER REFERENCES users(id),
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);