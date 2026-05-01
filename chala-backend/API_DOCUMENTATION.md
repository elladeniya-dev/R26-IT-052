# Chala Backend API Documentation

## Project

Smart Fashion Assistant: Intelligent Personalized and Trend-Aware Fashion Recommendation System

## Component

User Profiling, Google Sign-In Authentication, Onboarding, User Interactions, and User Learning Engine

## Base URL for Local Development

```text
http://127.0.0.1:8000
```

---

# 1. Health Check API

## Endpoint

```http
GET /health
```

## Authentication

Not required.

## Purpose

Checks whether the backend server is running.

## Sample Response

```json
{
  "status": "ok",
  "database": "connected",
  "module": "user-profiling-chalani"
}
```

---

# 2. Google Sign-In API

## Endpoint

```http
POST /auth/google
```

## Authentication

Not required.

## Purpose

Receives a Google ID token from the frontend or mobile app, verifies it, creates or finds the user in PostgreSQL, and returns the backend JWT token.

## Request Body

```json
{
  "token": "GOOGLE_ID_TOKEN_HERE"
}
```

## Sample Response

```json
{
  "access_token": "BACKEND_JWT_TOKEN_HERE",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "google_sub": "google-user-id",
    "full_name": "User Name",
    "email": "user@gmail.com",
    "profile_picture": "https://profile-picture-url",
    "auth_provider": "google"
  }
}
```

## Flutter Note

Flutter should send the Google ID token to this API.  
The returned `access_token` should be stored securely and used for protected APIs.

---

# 3. Get Logged-In User API

## Endpoint

```http
GET /auth/me
```

## Authentication

Required.

Use the backend JWT token in the Authorization header:

```http
Authorization: Bearer BACKEND_JWT_TOKEN_HERE
```

## Purpose

Returns the currently logged-in user based on the JWT token.

## Sample Response

```json
{
  "user_id": 1,
  "full_name": "User Name",
  "email": "user@gmail.com",
  "auth_provider": "google"
}
```

---

# 4. Save Onboarding Preferences API

## Endpoint

```http
POST /onboarding
```

## Authentication

Required.

```http
Authorization: Bearer BACKEND_JWT_TOKEN_HERE
```

## Purpose

Saves or updates the logged-in user's onboarding preferences.

## Request Body

```json
{
  "preferred_categories": ["Tops", "Dresses"],
  "preferred_colors": ["Black", "White"],
  "preferred_styles": ["Casual", "Elegant"],
  "price_min": 2000,
  "price_max": 10000,
  "occasions": ["Daily wear", "Party"],
  "preferred_patterns": ["Plain / solid", "Floral"],
  "extra_preferences": {}
}
```

## Sample Response

```json
{
  "preference_id": 1,
  "user_id": 1,
  "preferred_categories": ["Tops", "Dresses"],
  "preferred_colors": ["Black", "White"],
  "preferred_styles": ["Casual", "Elegant"],
  "price_min": 2000,
  "price_max": 10000,
  "occasions": ["Daily wear", "Party"],
  "preferred_patterns": ["Plain / solid", "Floral"],
  "extra_preferences": {}
}
```

---

# 5. Get User Profile API

## Endpoint

```http
GET /profile
```

## Authentication

Required.

```http
Authorization: Bearer BACKEND_JWT_TOKEN_HERE
```

## Purpose

Returns logged-in user details, onboarding preferences, and learned preferences.

## Sample Response

```json
{
  "user": {
    "user_id": 1,
    "google_sub": "google-user-id",
    "full_name": "User Name",
    "email": "user@gmail.com",
    "profile_picture": "https://profile-picture-url",
    "auth_provider": "google"
  },
  "onboarding_preferences": {
    "preference_id": 1,
    "user_id": 1,
    "preferred_categories": ["Tops", "Dresses"],
    "preferred_colors": ["Black", "White"],
    "preferred_styles": ["Casual", "Elegant"],
    "price_min": 2000,
    "price_max": 10000,
    "occasions": ["Daily wear", "Party"],
    "preferred_patterns": ["Plain / solid", "Floral"],
    "extra_preferences": {}
  },
  "learned_preferences": {
    "learned_id": 1,
    "user_id": 1,
    "category_weights": {
      "Tops": 0.75,
      "Shirts": 1.0,
      "Dresses": 0.75
    },
    "color_weights": {
      "Blue": 1.0,
      "Black": 0.75,
      "White": 0.75
    },
    "style_weights": {
      "Casual": 0.75,
      "Formal": 1.0,
      "Elegant": 0.75
    },
    "brand_weights": {
      "H&M": 1.0
    }
  }
}
```

---

# 6. Save User Interaction API

## Endpoint

```http
POST /interactions
```

## Authentication

Required.

```http
Authorization: Bearer BACKEND_JWT_TOKEN_HERE
```

## Purpose

Saves user actions on fashion items.

Supported interaction types:

```text
view
click
save
select
dislike
```

## Interaction Weight Mapping

| Interaction Type | Meaning | Weight |
|---|---|---|
| view | Weak interest | 1 |
| click | Medium interest | 2 |
| save | Strong interest | 3 |
| select | Very strong interest | 4 |
| dislike | Negative interest | -2 |

## Request Body

```json
{
  "item_id": "P001",
  "interaction_type": "click"
}
```

## Sample Response

```json
{
  "interaction_id": 1,
  "user_id": 1,
  "item_id": "P001",
  "interaction_type": "click",
  "interaction_value": 2.0
}
```

---

# 7. Insert Sample Products API

## Endpoint

```http
POST /products/sample
```

## Authentication

Not required for testing.

## Purpose

Inserts sample product records for testing Chala's Learning Engine.

This is temporary. Later, Koji's crawler or recommendation module will insert real product data into the `products` table.

## Sample Response

```json
{
  "message": "Sample products processed successfully",
  "inserted_count": 5,
  "skipped_count": 0
}
```

---

# 8. Update Learned Preferences API

## Endpoint

```http
POST /learning/update
```

## Authentication

Required.

```http
Authorization: Bearer BACKEND_JWT_TOKEN_HERE
```

## Purpose

Reads the logged-in user's saved interactions, fetches product details from the `products` table, calculates learned preference weights, and saves them in PostgreSQL.

## Sample Response

```json
{
  "message": "Learned preferences created successfully",
  "learned_preferences": {
    "learned_id": 1,
    "user_id": 1,
    "category_weights": {
      "Tops": 0.75,
      "Shirts": 1.0,
      "Dresses": 0.75
    },
    "color_weights": {
      "Blue": 1.0,
      "Black": 0.75,
      "White": 0.75
    },
    "style_weights": {
      "Casual": 0.75,
      "Formal": 1.0,
      "Elegant": 0.75
    },
    "brand_weights": {
      "H&M": 1.0
    }
  }
}
```

## Notes

The exact weight values can change depending on the user's saved interactions.

If learned preferences already exist, the response message may say:

```json
{
  "message": "Learned preferences updated successfully"
}
```

If the user has no interactions, the response may be:

```json
{
  "message": "No interactions found for this user",
  "learned_preferences": null
}
```

---

# Flutter Integration Flow

The Flutter app should follow this order:

```text
1. User signs in with Google in Flutter.
2. Flutter receives the Google ID token.
3. Flutter sends the Google ID token to POST /auth/google.
4. Backend returns backend JWT access_token.
5. Flutter stores the backend JWT token securely.
6. Flutter uses the backend JWT token for protected APIs.
7. User completes onboarding using POST /onboarding.
8. Flutter fetches profile using GET /profile.
9. When user views, clicks, saves, selects, or dislikes items, Flutter calls POST /interactions.
10. Backend updates learned preferences using POST /learning/update.
```

---

# Important Notes

- Flutter should use the backend JWT token for protected APIs.
- Do not send `user_id` from Flutter for protected APIs.
- Backend identifies the user from the JWT token.
- Google ID token is used only for login.
- Backend JWT token is used for app API access.
- `POST /products/sample` is temporary for backend testing.
- Real products will later come from Koji's product data collection module.
- The Learning Engine currently uses a weighted rule-based approach.
- H&M dataset purchase behavior can later be mapped as a strong positive interaction.

---

# Current Backend Status

Completed backend features:

```text
Google Sign-In backend authentication
JWT protected APIs
Onboarding preference saving
User profile retrieval
User interaction tracking
Sample product insertion
Learning Engine weight calculation
Learned preference saving
API documentation for Flutter integration
```