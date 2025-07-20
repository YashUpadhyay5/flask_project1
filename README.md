# Flask Content Management System (CMS)

## Project Overview
This is a simple Content Management System (CMS) built with Flask. It provides RESTful APIs for managing articles, user authentication with JWT, and a recently viewed feature. The app uses SQLite for storage and is fully containerized with Docker.

## Features
- RESTful API for articles (CRUD)
- User authentication with JWT (register/login)
- Each user can only access their own articles
- Recently viewed articles per user (in-memory, not persisted)
- SQLite database (file-based)
- Pagination for article listing
- Dockerized for easy deployment
- Alembic migrations scaffolded
- Unit tests for core functionality

## Getting Started

### Running Locally (with virtualenv)

1. **Clone the repo**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize the database:**
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```
5. **Run the app:**
   ```bash
   python app.py
   ```
   The app will be available at [http://localhost:5000](http://localhost:5000)

### Running with Docker

1. **Build and start the containers:**
   ```bash
   docker-compose up --build
   ```
2. **The app will be available at** [http://localhost:5000](http://localhost:5000)

### Running the Tests

1. **(If running locally)** Make sure your virtual environment is activated and dependencies are installed.
2. **Run:**
   ```bash
   pytest
   ```

## API Usage

### Authentication Flow
1. **Register a user:**
   ```bash
   curl -X POST http://localhost:5000/register -H "Content-Type: application/json" -d '{"username": "alice"}'
   ```
2. **Login to get a JWT token:**
   ```bash
   curl -X POST http://localhost:5000/login -H "Content-Type: application/json" -d '{"username": "alice"}'
   # Response: {"token": "<JWT_TOKEN>"}
   ```
3. **Use the token:**
   For all protected endpoints, add a header:
   ```
   Authorization: Bearer <JWT_TOKEN>
   ```
   Example with curl:
   ```bash
   curl -X GET http://localhost:5000/articles -H "Authorization: Bearer <JWT_TOKEN>"
   ```

### API Endpoints
- `POST /register` (JSON: username) — Register a new user
- `POST /login` (JSON: username) — Get JWT token
- `POST /articles` (JWT required, JSON: title, content)
- `GET /articles/<id>` (JWT required)
- `PUT /articles/<id>` (JWT required, JSON: title/content)
- `DELETE /articles/<id>` (JWT required)
- `GET /articles` (JWT required, supports `?page=1&limit=10`)
- `GET /recently_viewed` (JWT required)

#### Pagination
- Use `/articles?page=1&limit=10` to paginate article results.

## Notes
- Recently viewed articles are not persisted and reset on server restart.
- SQLite DB file is `cms.db` in the app directory.
- Change `SECRET_KEY` in `app.py` for production use. 