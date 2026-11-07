import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/intelligence"

def test_api():
    print("=== 1. TESTING EN-IN FACILITIES ===")
    r_en = requests.get(f"{BASE_URL}/facilities?language=en-IN")
    print("Status:", r_en.status_code)
    data_en = r_en.json()
    print("Count:", len(data_en))
    for f in data_en:
        fb = f.get("is_fallback", {})
        print(f"ID {f['id']}:")
        print(f"  Name: '{f['name']}' (is_fallback={fb.get('name')})")
        print(f"  Location: '{f['location']}' (is_fallback={fb.get('location')})")
        print(f"  Description: '{f['description']}' (is_fallback={fb.get('description')})")
        print(f"  Demo: {f['is_demo']} | Verified: {f['is_verified']}")

    print("\n=== 2. TESTING MR-IN FACILITIES ===")
    r_mr = requests.get(f"{BASE_URL}/facilities?language=mr-IN")
    print("Status:", r_mr.status_code)
    data_mr = r_mr.json()
    for f in data_mr:
        fb = f.get("is_fallback", {})
        print(f"ID {f['id']}:")
        print(f"  Name: '{f['name']}' (is_fallback={fb.get('name')})")
        print(f"  Location: '{f['location']}' (is_fallback={fb.get('location')})")

    print("\n=== 3. TESTING HI-IN FACILITIES ===")
    r_hi = requests.get(f"{BASE_URL}/facilities?language=hi-IN")
    print("Status:", r_hi.status_code)
    data_hi = r_hi.json()
    for f in data_hi:
        fb = f.get("is_fallback", {})
        print(f"ID {f['id']}:")
        print(f"  Name: '{f['name']}' (is_fallback={fb.get('name')})")
        print(f"  Location: '{f['location']}' (is_fallback={fb.get('location')})")

    print("\n=== 4. TESTING ASSISTANT CHAT EN-IN ===")
    chat_payload = {"message": "Where can I find drinking water?", "language": "en-IN"}
    r_chat = requests.post(f"{BASE_URL}/chat", json=chat_payload)
    print("Chat Status:", r_chat.status_code)
    chat_data = r_chat.json()
    print("Response text:", chat_data.get("response_text"))
    chat_facs = chat_data.get("facilities", [])
    print(f"Facilities returned in chat ({len(chat_facs)}):")
    for cf in chat_facs:
        fb = cf.get("is_fallback", {})
        print(f"  ID {cf['id']}: '{cf['name']}' at '{cf['location']}' (fallback={fb.get('name')})")

if __name__ == "__main__":
    test_api()
