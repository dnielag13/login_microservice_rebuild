# login_microservice

This microservice provides user authentication and account management functionality for a distributed application. It allows a client program to create user accounts, authenticate users, retrieve profile information, validate active sessions, and terminate sessions when necessary.

Authentication is handled using bearer tokens issued during login. Tokens are stored in memory and automatically expire after one hour to enforce session security.

All communication occurs over HTTP using JSON request and response bodies.

---

## Communication Contract

The following sections describe how to send requests to the microservice and how responses are returned.

---

## 1. Create User

Creates a new user account and securely stores the credentials.

Request  
Method: POST  
Route: /users  
Headers: Content-Type: application/json  

Body Example:
```json
{
  "user_id": "test_user",
  "password": "pass1234",
  "display_name": "Test User"
}
```

Example curl call:
```bash
curl -X POST http://127.0.0.1:5002/users \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","password":"pass1234","display_name":"Test User"}'
```

Successful Response (200):
```json
{
  "ok": true,
  "user": {
    "user_id": "test_user",
    "display_name": "Test User"
  }
}
```

If the user already exists or input validation fails, a 400-level error will be returned.

---

## 2. User Login

Authenticates a user and returns a session token.

Request  
Method: POST  
Route: /login  
Headers: Content-Type: application/json  

Body Example:
```json
{
  "user_id": "test_user",
  "password": "pass1234"
}
```

Example curl call:
```bash
curl -X POST http://127.0.0.1:5002/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","password":"pass1234"}'
```

Successful Response (200):
```json
{
  "ok": true,
  "token": "RANDOM_GENERATED_TOKEN",
  "user_id": "test_user"
}
```

If credentials are incorrect, the service responds with status 401 Unauthorized.

---

## 3. Get Current User

Returns the authenticated user's profile information. A valid bearer token is required.

Request  
Method: GET  
Route: /me  
Headers: Authorization: Bearer <token>

Example:
```bash
curl http://127.0.0.1:5002/me \
  -H "Authorization: Bearer RANDOM_GENERATED_TOKEN"
```

Successful Response (200):
```json
{
  "ok": true,
  "user": {
    "user_id": "test_user",
    "display_name": "Test User"
  }
}
```

If the token is invalid or expired (sessions automatically expire after one hour), a 401 error is returned.

---

## 4. Get Public User Profile

Returns public profile information for a specified user. This endpoint does not require authentication.

Request  
Method: GET  
Route: /users/{user_id}

Example:
```bash
curl http://127.0.0.1:5002/users/test_user
```

Response:
```json
{
  "user_id": "test_user",
  "display_name": "Test User"
}
```

If the user does not exist, a 404 error is returned.

---

## 5. Validate Token

Validates whether a provided authentication token is currently active.

Request  
Method: GET  
Route: /validate  
Headers: Authorization: Bearer <token>

Example:
```bash
curl http://127.0.0.1:5002/validate \
  -H "Authorization: Bearer RANDOM_GENERATED_TOKEN"
```

Successful Response (200):
```json
{
  "ok": true,
  "user_id": "test_user"
}
```

If the token is invalid or expired, a 401 Unauthorized response is returned.

---

## 6. Logout

Invalidates an active session token and removes it from memory.

Request  
Method: POST  
Route: /logout  
Headers: Authorization: Bearer <token>

Example:
```bash
curl -X POST http://127.0.0.1:5002/logout \
  -H "Authorization: Bearer RANDOM_GENERATED_TOKEN"
```

Successful Response (200):
```json
{
  "ok": true,
  "message": "Logged out"
}
```

After logout, any attempt to reuse the same token will result in a 401 Unauthorized error.

---

## 7. Ping Endpoint

A simple echo endpoint used to demonstrate request and response behavior.

Request  
Method: POST  
Route: /ping  
Headers: Content-Type: application/json  

Body Example:
```json
{
  "message": "This is a message from CS361"
}
```

Example:
```bash
curl -X POST http://127.0.0.1:5002/ping \
  -H "Content-Type: application/json" \
  -d '{"message":"This is a message from CS361"}'
```

Response:
```json
{
  "message": "This is a message from CS361"
}
```

---

## UML Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant LoginService

    Client->>LoginService: POST /users (create account)
    LoginService-->>Client: 200 OK

    Client->>LoginService: POST /login (credentials)
    LoginService-->>Client: 200 OK (token issued)

    Client->>LoginService: GET /validate (Bearer token)
    LoginService-->>Client: 200 OK (token valid)

    Client->>LoginService: GET /me (Bearer token)
    LoginService-->>Client: 200 OK (user profile)

    Client->>LoginService: POST /logout (Bearer token)
    LoginService-->>Client: 200 OK (session ended)
```

---

## How to Start the Service

1. Install dependencies:

```
pip install -r requirements.txt
```

2. Start the server:

```
python -m uvicorn main:app --host 127.0.0.1 --port 5002 --reload
```

You should see:

```
Uvicorn running on http://127.0.0.1:5002
```

3. Open the interactive API documentation:

```
http://127.0.0.1:5002/docs
```

To stop the server, press:

```
CTRL + C
```
