import sys
import requests

BASE_URL = "http://127.0.0.1:5002"

def main():
    print("=== Login Microservice Test Client ===")
    print(f"Target: {BASE_URL}/login\n")

    user_id = input("Enter user_id: ").strip()
    password = input("Enter password: ").strip()

    if not user_id or not password:
        print("\n❌ user_id and password are required.")
        sys.exit(1)

    payload = {"user_id": user_id, "password": password}

    try:
        r = requests.post(f"{BASE_URL}/login", json=payload, timeout=5)

        print("\n=== Response ===")
        print("Status:", r.status_code)

        try:
            data = r.json()
            print("JSON:", data)
        except ValueError:
            print("Body:", r.text)
            sys.exit(1)

        if r.status_code == 200 and data.get("ok") is True:
            print("\n✅ Login successful")
            print("user_id:", data.get("user_id"))
            print("token:", data.get("token"))
        else:
            print("\n❌ Login failed")
            if "detail" in data:
                print("detail:", data["detail"])

    except requests.exceptions.ConnectionError:
        print("\n🚨 Could not connect to the login microservice.")
        print(f"Is it running at {BASE_URL}?")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n🚨 Request timed out.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("\n🚨 Request error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()