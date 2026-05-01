# Chala Backend - User Profiling Component

## Project

Smart Fashion Assistant: Intelligent Personalized and Trend-Aware Fashion Recommendation System

## Component Overview

This backend belongs to Chala's component of the research project.

It handles:

- Google Sign-In backend authentication
- JWT protected APIs
- User onboarding preferences
- User profile retrieval
- User interaction tracking
- User Learning Engine
- Learned preference weight calculation

---

## Technology Stack

- Python 3.11.9
- FastAPI
- PostgreSQL 16.x
- SQLAlchemy
- JWT Authentication
- Google OAuth 2.0 / OpenID Connect
- pgAdmin 4
- Postman / Swagger for API testing

---

## Project Structure

```text
chala-backend/
│
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── learning_engine.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── .env.example
├── .gitignore
├── API_DOCUMENTATION.md
├── README.md
└── requirements.txt
```

---

## Database

Database used:

```text
fashion_assistant
```

Database system:

```text
PostgreSQL 16.x
```

---

## Environment Variables

Create a `.env` file inside `chala-backend`.

Use `.env.example` as the sample format.

Example:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/fashion_assistant

GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID

JWT_SECRET_KEY=YOUR_LONG_RANDOM_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Important:

- Do not upload `.env` to GitHub.
- `.env` contains private local configuration values.
- Only `.env.example` should be committed.

---

## Setup Instructions

### 1. Open project folder

```bash
cd chala-backend
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run FastAPI server

```bash
uvicorn app.main:app --reload
```

### 6. Open Swagger API documentation

```text
http://127.0.0.1:8000/docs
```

---

## Main API Features

| Feature | Endpoint |
|---|---|
| Health check | `GET /health` |
| Google Sign-In | `POST /auth/google` |
| Get logged-in user | `GET /auth/me` |
| Save onboarding preferences | `POST /onboarding` |
| Get user profile | `GET /profile` |
| Save user interaction | `POST /interactions` |
| Insert sample products | `POST /products/sample` |
| Update learned preferences | `POST /learning/update` |

Full API details are available in:

```text
API_DOCUMENTATION.md
```

---

## Interaction Weight Mapping

| Interaction Type | Meaning | Weight |
|---|---|---|
| view | Weak interest | 1 |
| click | Medium interest | 2 |
| save | Strong interest | 3 |
| select | Very strong interest | 4 |
| dislike | Negative interest | -2 |
| H&M purchase | Strong positive interest | 5 |

---

## Learning Engine

The Learning Engine currently uses a weighted rule-based approach.

Example:

```text
User clicks product P001.
P001 = Tops, Black, Casual.
click = 2.

Therefore:
Tops +2
Black +2
Casual +2
```

The final learned preferences are normalized between 0 and 1 and stored in:

```text
user_learned_preferences
```

Example output:

```json
{
  "category_weights": {
    "Tops": 0.75,
    "Shirts": 1.0
  },
  "color_weights": {
    "Black": 0.75,
    "Blue": 1.0
  },
  "style_weights": {
    "Casual": 0.75,
    "Formal": 1.0
  }
}
```

---

## Flutter Integration Summary

Flutter should follow this process:

```text
1. User signs in with Google in Flutter.
2. Flutter gets Google ID token.
3. Flutter sends Google ID token to POST /auth/google.
4. Backend verifies token and returns backend JWT token.
5. Flutter stores backend JWT token securely.
6. Flutter sends backend JWT token in protected API requests.
7. User completes onboarding.
8. User interactions are sent to backend.
9. Learning Engine updates learned preferences.
```

---

## Important Notes

- This backend uses Google Sign-In instead of normal email/password login.
- Backend JWT token is used for protected APIs.
- `user_id` should not be sent from Flutter for protected APIs.
- The backend identifies the user from the JWT token.
- `POST /products/sample` is only for local testing.
- Real product data will later come from Koji's product collection module.
- H&M dataset can later be used for purchase-based learning or model training.