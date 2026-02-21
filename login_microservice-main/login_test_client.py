"""
login_test_client.py

Test program for your Login Microservice:
- Create a user (POST /users)
- Login (POST /login)
- Optionally verify token (GET /me)

Use this for your video to show:
1) Test program requests data from microservice
2) Microservice responds with data
3) Test program receives/parses the response
4) Test program and microservice are NOT directly calling each other (HTTP only)

How to run:
  python login_test_client.py

Before running:
  - Start the login microservice
  - Set AUTH_BASE to your service URL (Codespaces URL or localhost)
"""

from __future__ import annotations

import sys
import requests

# ✅ Set this to your login microservice base URL.
# Examples:
# AUTH_BASE = "http://127.0.0.1:5002"
AUTH_BASE = "https://refactored-space-winner-4j54wvq4wq992qxgr-5002.app.github.dev"



def _prompt_nonempty(label: str) -> str:
    while True:
        s = input(label).strip()
        if s:
            return s
        print("Value cannot be blank.\n")


def _print_response(r: requests.Response) -> None:
    print("\n=== Microservice Response ===")
    print("Status:", r.status_code)
    try:
        print("JSON:", r.json())
    except ValueError:
        print("Body:", r.text)


def create_user() -> None:
    print("\n-------------------------------")
    print(" CREATE USER  (POST /users)")
    print("-------------------------------")

    user_id = _prompt_nonempty("Enter new user_id: ")
    password = _prompt_nonempty("Enter password: ")
    display_name = _prompt_nonempty("Enter display_name: ")

    try:
        r = requests.post(
            f"{AUTH_BASE}/users",
            json={"user_id": user_id, "password": password, "display_name": display_name},
            timeout=10,
        )
        _print_response(r)
    except requests.exceptions.RequestException as e:
        print("\n🚨 Could not reach microservice:", e)


def login() -> str:
    print("\n-------------------------------")
    print(" LOGIN  (POST /login)")
    print("-------------------------------")

    user_id = _prompt_nonempty("Enter user_id: ")
    password = _prompt_nonempty("Enter password: ")

    try:
        r = requests.post(
            f"{AUTH_BASE}/login",
            json={"user_id": user_id, "password": password},
            timeout=10,
        )
        _print_response(r)

        if r.status_code == 200:
            data = r.json()
            if data.get("ok") is True and data.get("token"):
                print("\n✅ Login successful. Token received.")
                return str(data["token"])

        print("\n❌ Login failed.")
        return ""
    except requests.exceptions.RequestException as e:
        print("\n🚨 Could not reach microservice:", e)
        return ""


def me(token: str) -> None:
    print("\n-------------------------------")
    print(" ME  (GET /me)")
    print("-------------------------------")

    try:
        r = requests.get(
            f"{AUTH_BASE}/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        _print_response(r)
    except requests.exceptions.RequestException as e:
        print("\n🚨 Could not reach microservice:", e)


def main() -> None:
    print("========================================")
    print(" Login Microservice Test Program (VIDEO)")
    print("========================================")
    print("AUTH_BASE =", AUTH_BASE)
    print("\nNOTE: This program uses HTTP requests (requests library).")
    print("It does NOT import or call the microservice code directly.\n")

    token = ""

    while True:
        print("\nMenu:")
        print("1) Create User")
        print("2) Login")
        print("3) Verify Token (/me)")
        print("4) Exit")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            create_user()
        elif choice == "2":
            token = login()
        elif choice == "3":
            if not token:
                print("\n⚠️ No token yet. Please login first.")
            else:
                me(token)
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting.")
        sys.exit(0)