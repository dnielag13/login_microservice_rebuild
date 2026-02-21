import sys
import requests

BASE_URL = "http://127.0.0.1:5002"

def login_get_token(user_id: str, password: str) -> str | None:
    r = requests.post(f"{BASE_URL}/login", json={"user_id": user_id, "password": password}, timeout=5)
    data = r.json()
    if r.status_code == 200 and data.get("ok") is True:
        return data.get("token")
    print("Login failed:", data)
    return None

def call_me(token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/me", headers=headers, timeout=5)

    print("\n=== /me Response ===")
    print("Status:", r.status_code)
    try:
        print("JSON:", r.json())
    except ValueError:
        print("Body:", r.text)

def main():
    print("=== /me Test Client ===")
    user_id = input("Enter user_id: ").strip()
    password = input("Enter password: ").strip()

    if not user_id or not password:
        print("user_id and password required.")
        sys.exit(1)

    try:
        token = login_get_token(user_id, password)
        if not token:
            sys.exit(1)

        print("\n✅ Got token:", token)
        call_me(token)

    except requests.exceptions.RequestException as e:
        print("Request error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()