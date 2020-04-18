import requests

def login_epn():
    session_requests = requests.session()
    url = 'https://oauth2.epn.bz/ssid?client_id=web-client'
    source_code = session_requests.get(url, headers={"x-api-version": "2"})
    plain_text = source_code.json()
    ssid_token = plain_text['data']['attributes']['ssid_token']
    url = 'https://oauth2.epn.bz/token'
    payload = {
        "check_ip": "false",
        "client_id": "web-client",
        "client_secret": "CLIENTSECRET",
        "grant_type": "password",
        "password": "YOURPASSWORD",
        "ssid_token": ssid_token,
        "username": "email@email.com"
    }
    source_code = session_requests.post(url, data=payload, headers={"x-api-version": "2"})
    headers = source_code.headers
    plain_text = source_code.json()
    url = 'https://epn.bz/ru/cashback/payments'
    source_code = session_requests.get(url)
    plain_text = source_code.text