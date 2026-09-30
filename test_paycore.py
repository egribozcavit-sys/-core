import requests

BASE_URL = "http://localhost:8000"

def main():
    # 1) Kullanıcı oluştur
    register_payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test1234!"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
    print("Register:", r.status_code, r.json())

    # 2) Login -> token al
    login_payload = {
        "username": "testuser",
        "password": "Test1234!"
    }
    r = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
    print("Login:", r.status_code, r.json())
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3) Kendi kullanıcı bilgisini çek
    r = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print("Me:", r.status_code, r.json())
    user_id = r.json()["user_id"]

    # 4) Hesap aç
    account_payload = {"currency": "USD"}
    r = requests.post(f"{BASE_URL}/accounts/", json=account_payload, headers=headers)
    print("Create account:", r.status_code, r.json())
    account_id = r.json()["account_id"]

    # 5) İkinci kullanıcı ve hesap (receiver için)
    register_payload2 = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "Test1234!"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=register_payload2)
    print("Register 2:", r.status_code, r.json())

    login_payload2 = {
        "username": "testuser2",
        "password": "Test1234!"
    }
    r = requests.post(f"{BASE_URL}/auth/login", data=login_payload2)
    token2 = r.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    r = requests.post(f"{BASE_URL}/accounts/", json={"currency": "USD"}, headers=headers2)
    print("Create account 2:", r.status_code, r.json())
    account_id2 = r.json()["account_id"]

    # 6) İlk kullanıcı ile tekrar login (sender)
    r = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 7) Transfer oluştur
    transaction_payload = {
        "sender_account_id": account_id,
        "receiver_account_id": account_id2,
        "amount_cents": 1000,
        "currency": "USD",
        "transaction_type": "transfer",
        "description": "Test transfer",
        "idempotency_key": "test-transfer-1"
    }
    r = requests.post(f"{BASE_URL}/transactions/", json=transaction_payload, headers=headers)
    print("Create transaction:", r.status_code, r.json())
    transaction_id = r.json().get("transaction_id")

    # 8) Transfer durumunu sorgula
    if transaction_id:
        r = requests.get(f"{BASE_URL}/transactions/{transaction_id}", headers=headers)
        print("Transaction status:", r.status_code, r.json())

    # 9) Bakiye kontrolü
    r = requests.get(f"{BASE_URL}/accounts/{account_id}/balance", headers=headers)
    print("Sender balance:", r.status_code, r.json())

    r = requests.get(f"{BASE_URL}/accounts/{account_id2}/balance", headers=headers2)
    print("Receiver balance:", r.status_code, r.json())

    # 10) Aynı idempotency_key ile tekrar gönder (double-spend testi)
    r = requests.post(f"{BASE_URL}/transactions/", json=transaction_payload, headers=headers)
    print("Duplicate transaction:", r.status_code, r.json())

if __name__ == "__main__":
    main()
