# API Reference

## Authentication
All protected endpoints require a JWT token in the Authorization header:
`Authorization: Bearer <access_token>`

## Endpoints

### 1. Health Check
- **GET** `/health`
- **Response**: `200 OK` `{"status": "healthy", "timestamp": "..."}`

### 2. Register
- **POST** `/api/register`
- **Body**: `{"name": "...", "email": "...", "password": "...", "role": "student"}`
- **Response**: `201 Created`

### 3. Login
- **POST** `/api/login`
- **Body**: `{"email": "...", "password": "..."}`
- **Response**: `200 OK` `{"access_token": "...", "user": {...}}`

### 4. Query AI
- **POST** `/api/query`
- **Headers**: `Authorization: Bearer ...`
- **Body**: `{"question": "What is my attendance?"}`
- **Response**: `200 OK` `{"answer": "...", "confidence": 0.9, "intent": "attendance", "response_time_ms": 12.5}`

### 5. Get History
- **GET** `/api/history`
- **Headers**: `Authorization: Bearer ...`
- **Response**: `200 OK` Array of query objects.

### 6. Admin: Suspicious Users
- **GET** `/api/admin/suspicious`
- **Headers**: `Authorization: Bearer ...` (Must be admin)
- **Response**: `200 OK` Array of suspicious users.

### 7. Admin: Performance
- **GET** `/api/admin/performance`
- **Headers**: `Authorization: Bearer ...` (Must be admin)
- **Response**: `200 OK` Daily performance stats.
