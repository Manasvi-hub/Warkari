import requests

BASE_URL = "http://127.0.0.1:8000/api/intelligence"

chat_mr = requests.post(f"{BASE_URL}/chat", json={"message": "पिण्याचे पाणी कुठे मिळेल?", "language": "mr-IN"}).json()
print("MR Response:", chat_mr.get("response_text"))
for f in chat_mr.get("facilities", []):
    print("MR Fac:", f["name"], "-", f["location"])

chat_hi = requests.post(f"{BASE_URL}/chat", json={"message": "पीने का पानी कहाँ मिलेगा?", "language": "hi-IN"}).json()
print("\nHI Response:", chat_hi.get("response_text"))
for f in chat_hi.get("facilities", []):
    print("HI Fac:", f["name"], "-", f["location"])

