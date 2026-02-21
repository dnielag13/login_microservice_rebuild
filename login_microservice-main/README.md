# login_microservice
This microservice provides basic user account functionality for distributed applications. It allows clients program to: Create a user account, Authenticate and receive a session token, Retrieve user profile information, and Validate an authenticated session using a token. 

1. Create User
Creates a new user account.

Request
Method: POST
Route: /users
Headers: Content-Type: application/json
Request Data Example:
{
  "user_id": "test_user",
  "password": "pass1234",
  "display_name": "Test User"
}

Programmatic call:
curl -X POST http://127.0.0.1:5002/users \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","password":"pass1234","display_name":"Test User"}'

Response Example:
{
  "ok": true,
  "user": {
    "user_id": "test_user",
    "display_name": "Test User"
  }
}

2. User login
Authenticates a user and returns a session token.

Request
Method: POST
Route: /login
Headers: Content-Type: application/json

Request Data Example:
{
  "user_id": "test_user",
  "password": "pass1234"
}

Programmatic Call:
curl -X POST http://127.0.0.1:5002/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","password":"pass1234"}'

Response Example:
{
  "ok": true,
  "token": "RANDOM_GENERATED_TOKEN",
  "user_id": "test_user"
}

3. Get Current User
Returns the authenticated user's profile information.

Request
Method: GET
Route: /me
Headers: Authorization: Bearer RANDOM_GENERATED_TOKEN

Programmatic Call:
curl http://127.0.0.1:5002/me \
  -H "Authorization: Bearer RANDOM_GENERATED_TOKEN"

Response Example:
{
  "ok": true,
  "user": {
    "user_id": "test_user",
    "display_name": "Test User"
  }
}

4. Get Public User Profile
Returns a user’s public profile (no password).

Request
Method: GET
Route: /users/{user_id}

Example Call:
curl http://127.0.0.1:5002/users/test_user

Response Example:
{
  "user_id": "test_user",
  "display_name": "Test User"
}

5. Endpoint
Echo endpoint used to demonstrate request/response functionality.

Request
Method: POST
Route: /ping
{
 Example: "message": "This is a message from CS361"
}

Example Call:
curl -X POST http://127.0.0.1:5002/ping \
  -H "Content-Type: application/json" \
  -d '{"message":"This is a message from CS361"}'

Response Example:
{
  "message": "This is a message from CS361"
}

UML Sequence Diagram:
sequenceDiagram
    participant Client
    participant LoginService

    Client->>LoginService: POST /users (JSON user data)
    LoginService-->>Client: 200 OK (User created)

    Client->>LoginService: POST /login (credentials)
    LoginService-->>Client: 200 OK (token returned)

    Client->>LoginService: GET /me (Authorization: Bearer token)
    LoginService-->>Client: 200 OK (user profile)

How to start the code:
1. in a terminal paste this: pip install -r requirements.txt
2. Then run the server: python -m uvicorn main:app --host 127.0.0.1 --port 5002 --reload
You should see: Uvicorn running on http://127.0.0.1:5002
3. Open the Swagger docs: https://<your-codespace>-5002.app.github.dev/docs

To stop the server press: CTRL + C