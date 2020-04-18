import requests
from selenium import webdriver
import time
import urllib.parse


session_requests = requests.session()
start_time = None
x_access_token = ''


def login_epn():
    global session_requests
    try:
        url = 'https://oauth2.backit.me/ssid?client_id=web-client'
        source_code = session_requests.get(url, headers={"x-api-version": "2"})
        plain_text = source_code.json()
        ssid_token = plain_text['data']['attributes']['ssid_token']
        url = 'https://oauth2.backit.me/token'
        payload = {
            #"captcha": None,
            #"check_ip": "false",
            "client_id": "web-client",
            "client_secret": "CLIENTSECRET",
            "grant_type": "password",
            "password": "YOURPASSWORD",
            "ssid_token": ssid_token,
            "username": "email@email.com"
        }
        source_code = session_requests.post(url, data=payload, headers={"x-api-version": "2"})
        plain_text = source_code.json()
        access_token = plain_text['data']['attributes']['access_token']
        print(source_code)
        return access_token
    except Exception as e:
        print("Exception: " + str(e))
        return None


def get_cashback_cookies():
    driver = webdriver.Chrome('C:\\temp\\chromedriver.exe')
    driver.get('https://epn.bz/ru/cashback')
    driver.switch_to.frame(0)
    time.sleep(25)
    cookies_list = driver.get_cookies()
    return cookies_list

def get_cashback_link(cookies_list, url):
    global session_requests
    global start_time
    global x_access_token
    if not start_time:
        start_time = time.time()
        try:
            x_access_token = login_epn()
            if not x_access_token:
                return None
        except Exception as e:
            print("Exception: " + str(e))
            return None
    current_time = time.time()
    if current_time - start_time > 10*60:
        try:
            x_access_token = login_epn()
        except:
            return None
        start_time = time.time()
    #ALI_URL = 'https://www.aliexpress.com/item/Cowin-New-E7-Pro-BT-Game-Headphones-Gaming-Earphone-Stereo-Headset-Headphone-For-Travel-Work-TV/32916090288.html'
    #CASHBACK_URL = 'https://epn.bz/ru/cashback/get-referral-link'
    #for cookie in cookies_list:
    #    session_requests.cookies.set(cookie['name'], cookie['value'])
    #payload = {
    #    "link": url,
    #    "ref_type": "99"
    #}
    #CASHBACK_URL = 'https://app.epn.bz/affiliate/cashback/link?refOfferId=99&link=' + urllib.parse.quote_plus(url)
    CASHBACK_URL = 'https://app.backit.me/affiliate/cashback/link'
    payload = (('refOfferId', '99'), ('link', url))
    try:
        #source_code = session_requests.post(CASHBACK_URL, data=payload)
        source_code = session_requests.get(CASHBACK_URL, headers={"x-access-token": x_access_token}, params=payload)
        plain_text = source_code.json()
        #plain_text = source_code.text
        return plain_text['data']['attributes']['link']
    except:
        return None