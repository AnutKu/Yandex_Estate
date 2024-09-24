from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

def write(link):
    with open("data.txt", "a") as file:
        file.write(link + "\n")


def get_data(driver, links):
    driver.get("https://realty.ya.ru/moskva/")
    element = driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[4]/div[1]/div/div[3]/a")
    element.click()
    while len(links) < 1100:
        elements = driver.find_elements(By.XPATH,
                                        "/html/body/div[2]/div[3]/div[2]/div/div[3]/div/div[2]/ol/li/div/div/div[1]/div[1]/div[1]/a/div")
        for el in elements:
            parent = el.find_element(By.XPATH, "..")
            link = parent.get_attribute("href")
            if link not in links:
                write(link)
            links.add(link)
        wait = WebDriverWait(driver, 5)
        # Переходим на "следующая"
        link_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[@class='Pager__radio-link']")))
        if len(link_elements) > 5:
            link_element = link_elements[5]  # Первые пять квадратов с цифрами внизу, шестой-"следующая"
        else:
            link_element = link_elements[0]
        href_link = link_element.get_attribute('href')
        driver.get(href_link)
        print(len(links))
    driver.quit()
    return links



def get_uniques_links():
    with open('data.txt', 'r') as file:
        data = [elem.rstrip() for elem in file.readlines()]
        data = set(data)
        with open('data.txt', 'w') as file:
            for link in data:
                file.write(link + "\n")
        return data


def get_page_html(driver, url, wait_time=10):
    try:
        driver.get(url)
        # Ожидаем, пока ключевой элемент не загрузится
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))  # Ожидание загрузки тела страницы
        )
        return driver.page_source
    except TimeoutException:
        print(f"Ошибка таймаута для {url}")
        return None

def write_html(driver, links, download_files):
    for url in links:
        filename = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.html'
        if filename not in download_files:
            try:
                html = get_page_html(driver, url)
                if html:

                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(html)
                else:
                    print(f"Не удалось получить содержимое для {url}")
            except Exception as e:
                print(f"Ошибка при работе с {url}: {e}")



driver = webdriver.Firefox()
links = get_uniques_links()
# get_data(driver, links)
path = 'D:\\3_курс_5_семестр\\Анализ_данных'
download_files = os.listdir(path)
write_html(driver, links, download_files)


