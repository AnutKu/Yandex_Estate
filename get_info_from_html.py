import lxml.html
import os
import re
import openai
import json



def read(parsefile):
    with open(os.path.join(path, parsefile), 'r', encoding='utf-8') as file:
        html = file.read()
        html_tree = lxml.html.fromstring(html)
    return html_tree


def get_square_roomquantity_typeofestate(html_tree):
    # Извлекаем текст из элемента
    data = html_tree.xpath('//h1[@class="OfferCardSummaryInfo__description--3-iC7"]/text()')[0]
    pattern_square = r'(\d+)\Wм²'
    pattern_room = r'(\d+)-комнат'
    pattern_type = r'(\w+)$'
    square = re.search(pattern_square, data).group(1)
    typeestate = re.search(pattern_type, data).group(1)
    if "студия" in typeestate:
        room = 1
    else:
        room = re.search(pattern_room, data).group(1)  # 1 чтобы выводило только то, что в скобках
    return square, room, typeestate

def get_price(html_tree):
    data = html_tree.xpath('//span[@class="OfferCardSummaryInfo__price--2FD3C OfferCardSummaryInfo__priceWithLeftMargin--3I6Y8"]/text()')[0]
    pattern_price = r'^.*?(?=₽)'
    price = re.search(pattern_price, data).group(0)
    price = price.split()
    price_st = ''
    for el in price:
        price_st += el
    price = int(price_st)
    return price


def get_deposit(html_tree):
    data = html_tree.xpath('//span[@class="OfferCardCheck__rowValue--bcPJA"]/text()')[0]
    if 'есть' in data:
        return True, None
    pattern_deposit= r'^.*?(?=₽)'
    deposit = re.search(pattern_deposit, data).group(0).split()
    deposit_st = ''
    for el in deposit:
        deposit_st += el
    if '0' == deposit_st:
        return False, 0
    return True, int(deposit_st)


def get_adress(html_tree):
    try:
        data = html_tree.xpath('//div[@class="CardLocation__addressItem--1JYpZ"]/text()')[0]

        openai.api_key = "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"
        messages = [
            {
                "role": "user",
                "content": f"Я работаю с данными о съемных квартирах и нуждаюсь в помощи с их очисткой."
                           f" Я передам строку с адресом, а тебе нужно извлечь три параметра:"
                           f" 1. Город (или поселок/деревню)"
                           f" 2. Улицу (включая переулок/шоссе/бульвар/проспект/проезд)"
                           f" 3. Номер дома (включая букву 'к' для корпуса, а также символы '/' или '-')"
                           f" Верни три значения, разделенные символом '*', без лишних пробелов и запятых."
                           f" Если какой-то параметр отсутствует, верни 'None'."
                           f" Например, 'Москва, Ленинский проспект, д. 12к1' -> 'Москва*Ленинский проспект*12к1'."
                           f" Если вернешь больше или меньше трех параметров или добавишь запятые, мой код упадет с ошибкой."
                           f" Вот строка для обработки: {data}"
            }
        ]
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100
        )
        decoded_response = completion.choices[0].message['content']
        ans = decoded_response.split('*')
        return ans[0], ans[1], ans[2]

    except Exception as e:
        print(f'Произошла ошибка: {e}')

def get_station(html_tree): # метро или станция электрички поблизости
    data = html_tree.xpath('//span[@class="MetroStation__title"]/text()')
    if len(data) > 0:
        data = data[0]
    else:
        data = None
    return data

def get_time_to_station(html_tree):
    data = html_tree.xpath('//span[contains(@class, "stationDistance")]/span[1]/text()')
    if len(data) > 0:
        pattern_time = r'^.*?(?=мин.)'
        time =int(re.search(pattern_time, data[0]).group(0))
    else:
        time = None
    return time


def get_tech_info(html_tree):
    parent_div = html_tree.xpath(
        '//div[contains(@class, "OfferCard__techFeatures--3Zoaa") and contains(@class, "OfferCardHighlights__container--1klL_")]')
    if parent_div:
        # Получаем все дочерние div элементы
        child_divs = parent_div[0].xpath('.//div')
        live_square, kitchen_square, floornum, floorquant, ceilingsheight, builtyear = None, None, None, None, None, None
        for i in range(0, len(child_divs),3): # раз в три из-за дублирования
            line = child_divs[i].text_content().strip()
            if "жилая" in line:
                line = line.split()
                live_square = float(line[0].replace(',', '.'))
            elif "кухня" in line:
                line = line.split()
                kitchen_square = float(line[0].replace(',', '.'))
            elif "этаж" in line:
                if "из" in line:
                    line = line.split()
                    floornum, floorquant = int(line[0]), int(line[-1])
                else:
                    line = line.split()
                    floornum = int(line[0])
            elif "потолки" in line:
                line = line.split()
                ceilingsheight = float(line[0].replace(',', '.'))
            elif "год" in line:
                line = line.split()
                builtyear = int(line[0])
        return live_square, kitchen_square, floornum, floorquant, ceilingsheight, builtyear
    else:
        print("Родительский div не найден")


def fill_dic(parsed_files):
    dataforeverypage = {}
    for parsefile in parsed_files:
        html_tree = read(parsefile)
        dic = {}
        city, street, numhouuse = get_adress(html_tree)
        dic['Насёленный пункт'], dic['Улица'], dic['Номер дома'] = city, street, numhouuse
        station = get_station(html_tree)
        dic['Ближайшая станция рядом'] = station
        time_to_station = get_time_to_station(html_tree)
        dic['Время до ближийшей станции(мин.)'] = time_to_station
        square, roomquant, typeofestate = get_square_roomquantity_typeofestate(html_tree)
        live_square, kitchen_square, floornum, floorquant, ceilingsheight, builtyear = get_tech_info(html_tree)
        dic['Тип недвижимости'], dic['Общая площадь(м^2)'], dic['Количество комнат'] = typeofestate, square, roomquant
        dic['Жилая площадь(м^2)'], dic['Площадь кухни(м^2)'] = live_square, kitchen_square
        price = get_price(html_tree)
        dic['Стоимость аренды в месяц(₽)'] = price
        has_deposit, deposit = get_deposit(html_tree)
        dic['Необходимо внести залог'], dic['Величина залога (₽)'] = has_deposit, deposit
        dic['Этаж'], dic['Всего этажей в доме'], dic['Высота потолков(м.)'], dic['Год постройки дома'] = floornum, floorquant, ceilingsheight, builtyear
        dataforeverypage[parsefile] = dic
    return dataforeverypage


def writeinjson(data):
    with open('realty_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4) # Параметр indent=4 используется для форматирования JSON файла с отступами для улучшения читаемости.

path = './Спаршенные данные'
parsed_files = os.listdir(path)
data = fill_dic(parsed_files)
print("Заполнение завершено")
writeinjson(data)