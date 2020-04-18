from bs4 import BeautifulSoup
import requests
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import json
import time
import os
import pyautogui
from scipy import interpolate
import random
import scipy

PAGE_NUMBER = 10

#search_url = 'https://www.aliexpress.com/wholesale?catId=0'

start_time = None
s = None
go_with_login = False


def get_chromedriver():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    path = os.path.dirname(os.path.abspath(__file__))
    driver = webdriver.Chrome(executable_path=os.path.join(path, 'chromedriver'), options=options)
    return driver


def real_move(x_final, y_final):
    cp = random.randint(3, 5)  # Number of control points. Must be at least 2.
    x1, y1 = pyautogui.position()  # Starting position
    x2, y2 = x_final, y_final  # Destination

    # Distribute control points between start and destination evenly.
    x = scipy.linspace(x1, x2, num=cp, dtype='int')
    y = scipy.linspace(y1, y2, num=cp, dtype='int')

    # Randomise inner points a bit (+-RND at most).
    RND = 20
    xr = scipy.random.randint(-RND, RND, size=cp)
    yr = scipy.random.randint(-RND, RND, size=cp)
    xr[0] = yr[0] = xr[-1] = yr[-1] = 0
    x += xr
    y += yr

    # Approximate using Bezier spline.
    degree = 3 if cp > 3 else cp - 1  # Degree of b-spline. 3 is recommended.
    # Must be less than number of control points.
    tck, u = scipy.interpolate.splprep([x, y], k=degree)
    #u = scipy.linspace(0, 1, num=max(pyautogui.size()))
    u = scipy.linspace(0, 1, num=max(pyautogui.size()))
    points = scipy.interpolate.splev(u, tck)

    # Move mouse.
    duration = 0.001
    timeout = duration / len(points[0])
    # Any duration less than this is rounded to 0.0 to instantly move the mouse.
    pyautogui.MINIMUM_DURATION = 0  # Default: 0.1
    # Minimal number of seconds to sleep between mouse moves.
    pyautogui.MINIMUM_SLEEP = 0  # Default: 0.05
    # The number of seconds to pause after EVERY public function call.
    pyautogui.PAUSE = 0  # Default: 0.1
    for point in zip(*(i.astype(int) for i in points)):
        pyautogui.moveTo(*point)
        #time.sleep(timeout)


def login_ali(with_login=False):
    driver = get_chromedriver()
    driver.get('https://login.aliexpress.com')
    #driver.switch_to.frame(0)
    username = driver.find_element_by_id("fm-login-id")
    sleep(1)
    username.send_keys('email@email.com')
    sleep(2)
    password = driver.find_element_by_id("fm-login-password")
    sleep(1)
    password.send_keys('YOURPASSWORD')
    sleep(2)
    submit = driver.find_element_by_class_name('fm-submit')
    current_url = driver.current_url
    submit.click()
    WebDriverWait(driver, 60).until(EC.url_changes(current_url))
    driver.switch_to.default_content()
    driver.get('https://www.aliexpress.com/wholesale?SearchText=test')
    WebDriverWait(driver, 60).until(EC.url_changes(current_url))
    #driver.switch_to.frame(0)
    try:
        submit = driver.find_element_by_class_name('fm-submit')
        current_url = driver.current_url
        submit.click()
        WebDriverWait(driver, 60).until(EC.url_changes(current_url))
    except Exception as e:
        print(e)
        pass
    try:
        driver.switch_to.default_content()
        elem_found = driver.find_element_by_id('nc_1_n1z')
    except Exception as e:
        print(e)
        elem_found = None
    cookies_list = driver.get_cookies()
    driver.quit()
    print(cookies_list)
    s = requests.Session()
    for cookie in cookies_list:
        s.cookies.set(cookie['name'], cookie['value'])
    return s


def find_refund(user_data, link_list, cond_result, cond_user):
    global start_time
    global s
    global go_with_login
    global PROXY_ID
    global PROXY_LIST
    SEARCH_URL = 'https://www.aliexpress.com/wholesale?SortType=create_desc'
    #SEARCH_URL = 'https://www.aliexpress.com/wholesale?SortType=default'
    #min_price = '10'
    #max_price = ''
    if user_data['min_price']:
        SEARCH_URL += '&minPrice=' + user_data['min_price']
    if user_data['max_price']:
        SEARCH_URL += '&maxPrice=' + user_data['max_price']
    SEARCH_URL += '&SearchText='
    #SEARCH_PRODUCT = 'mi band 3'
    #BRAND = 'xiaomi'
    search_url = SEARCH_URL + user_data['product']
    go_with_login = not go_with_login
    new_proxy = False
    while True:
        try:
            if not start_time:
                start_time = time.time()
                s = login_ali(True)
            current_time = time.time()
            if current_time - start_time > 20*60:
                s = login_ali(True)
                start_time = time.time()
        except Exception as e:
            print("Exception: " + str(e))
            start_time = None
            link_list.clear()
            link_list.append([-1])
            with cond_result:
                cond_result.notifyAll()
            exit()
        for page_num in range(1, PAGE_NUMBER):
            request_url = search_url + '&page=' + str(page_num)
            print(request_url)
            r = s.get(request_url)
            page = r.text
            soup = BeautifulSoup(page, 'html.parser')
            test_page = soup.find('div', attrs={'class': 'zero-list'})
            if test_page and page_num == 1:
                start_time = None
                link_list.clear()
                link_list.append(None)
                with cond_result:
                    cond_result.notifyAll()
                exit()
            prodlist = []
            products = re.findall(r'"productDetailUrl":"([^"]*)"', page)
            for p in products:
                prodlist.append('http://' + p[2:])
            prodlist_count = len(prodlist)
            print("Products found: " + str(prodlist_count))
            # in case of connection error we need to change proxy
            if prodlist_count == 0 and page_num == 1:
                print('0 products found, restart')
                start_time = None
                link_list.clear()
                link_list.append(None)
                with cond_result:
                    cond_result.notifyAll()
                exit()
            for p in prodlist:
                prod_page = requests.get(p).text
                soup_prod = BeautifulSoup(prod_page, 'html.parser')
                filter_found = False
                #title = soup_prod.find('div', attrs={'class': 'product-title'})
                title_search = re.search(r'"name":"TitleModule".*"subject":"([^"]*)"', prod_page)
                if title_search:
                    title = title_search.group(1)
                    if 'filter_words' in user_data:
                        for filtered_word in user_data['filter_words']:
                            if filtered_word.lower() in title.lower():
                            #print('filtered word found, so this is not our item!')
                                filter_found = True
                                break
                if filter_found:
                    continue
                brand_search = re.search(r'"attrName":"Brand Name".*?"attrValue":"([^"]*)"', prod_page)
                if not brand_search:
                    continue
                child = brand_search.group(1)
                if child.lower() not in user_data['brand']:
                    #return p
                    print(p)
                    link_list.clear()
                    link_list.append([p, child])
                    with cond_result:
                        cond_result.notifyAll()
                    with cond_user:
                        if not cond_user.wait(300):
                            exit()
                #else:
                #    print('brand fine!')
        if new_proxy == True:
            continue
        else:
            link_list.clear()
            link_list.append(None)
            with cond_result:
                cond_result.notifyAll()
            break


if __name__ == '__main__':
    try:
        find_refund(SEARCH_PRODUCT, BRAND)
    except KeyboardInterrupt:
        exit()
