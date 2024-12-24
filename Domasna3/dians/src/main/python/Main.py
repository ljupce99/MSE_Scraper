import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

import sys
import io
import requests
from bs4 import BeautifulSoup
import re
import json
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

csv_file_path = "./Smestuvanje/mega-data.csv"
json_file_path = "./Smestuvanje/issuer_names.json"
output_json = "./Smestuvanje/last_dates.json"
patjson="./Smestuvanje/issuer_names.json"
url = "https://www.mse.mk/mk/stats/symbolhistory/ALK"
pat="./Smestuvanje/mega-data.csv"




start_time = time.time()





directory = './Smestuvanje'
if not os.path.exists(directory):
    os.makedirs(directory)
    print(f"Папката '{directory}' е создадена.")


if not os.path.isfile(json_file_path):
    print(f"Фајлот '{json_file_path}' не постои.")
else:
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        print("Податоците се вчитани успешно.")


# URL на страницата
url_base45 = "https://www.mse.mk/mk/stats/current-schedule"

# Параметри за различните категории
categories = [
    {"name": "Континуирано (+/- 10%)", "url": url_base45 + "?category=10"},
    {"name": "Аукциско со ценовни ограничувања (+/- 20%)", "url": url_base45 + "?category=20"},
    {"name": "Аукциско без ценовни ограничувања", "url": url_base45 + "?category=no-limit"}
]

# Список за чување на податоци
data12 = []


# Функција за вчитување и извлекување на податоци од една категорија
def fetch_data_from_category(url):
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Грешка при барање на страницата: {response.status_code}")
        return []

    soup1 = BeautifulSoup(response.content, 'html.parser')

    # Пребарување на сите табели на страницата
    tables = soup1.find_all('table')

    category_data = []

    # Пребарување низ секоја табела
    for table in tables:
        rows = table.find_all('tr')

        for row in rows[1:]:  # Првиот ред е хедер, па го прескокнуваме
            columns = row.find_all('td')

            if len(columns) >= 3:
                # Извлекување на Шифра на ХВ и Опис на ХВ
                code = columns[0].get_text(strip=True)
                description = columns[1].get_text(strip=True)

                # Проверка дали "Шифра на ХВ" не содржи бројки
                if not re.search(r'\d', code):  # Проверка дали има бројки
                    category_data.append({
                        'Шифра на ХВ': code,
                        'Опис на ХВ': description
                    })

    return category_data

def fachNames():
    # Пребарување и собирање на податоци од сите категории
    for category in categories:
        print(f"Вчитување на податоци за категоријата: {category['name']}")
        category_data = fetch_data_from_category(category['url'])
        data12.extend(category_data)
    # Отстранување на дупликатите користејќи сет
    unique_data = []
    seen = set()

    for item in data12:
        code = item['Шифра на ХВ']
        description = item['Опис на ХВ']
        if (code, description) not in seen:
            unique_data.append(item)
            seen.add((code, description))

    # Запишување на податоците во JSON фајл
    output_dir = './Smestuvanje'
    os.makedirs(output_dir, exist_ok=True)  # Ако не постои папката, ја создава
    with open(os.path.join(output_dir, 'names.json'), 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print("Податоците успешно се зачувани во JSON.")


def fetch_codes_from_tabs(url):
    """Fetch the codes (Шифра на ХВ) from all three tabs on the page."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    tabs = soup.find_all('table', class_='table')
    if not tabs:
        print("No tabs found.")
        return {}

    codes_by_tab = {}
    tab_names = ["Континуирано (+/- 10%)", "Аукциско со ценовни ограничувања (+/- 20%)",
                 "Аукциско без ценовни ограничувања"]

    for i, tab in enumerate(tabs):
        codes = []
        rows = tab.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if columns:
                code = columns[0].text.strip()  # Assuming Шифра на ХВ is in the first column
                if code and not re.search(r'\d', code):  # Filter out codes containing numbers
                    codes.append(code)
        codes_by_tab[tab_names[i]] = codes

    return codes_by_tab

def Call_Filter_1():
    url = 'https://www.mse.mk/mk/stats/current-schedule'
    codes_by_tab = fetch_codes_from_tabs(url)
    if codes_by_tab:
        # Flatten all codes and assign unique IDs
        all_codes = [{"id": idx + 1, "name": code} for idx, code in enumerate(sum(codes_by_tab.values(), []))]
        with open(patjson, "w", encoding="utf-8") as file:
            json.dump(all_codes, file, indent=4, ensure_ascii=False)
        print("Issuer codes saved to 'issuer_names.json'.")
    Call_Filter_II()

def load_or_create_csv(csv_file):
    folder = os.path.dirname(csv_file)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")

    if not os.path.isfile(csv_file):
        headers = ["code", "date", "close", "max", "low", "avg", "changePerc", "volume", "turnover in BEST", "total turnover"]
        pd.DataFrame(columns=headers).to_csv(csv_file, index=False)
        print(f"Created CSV file: {csv_file}")

    return pd.read_csv(csv_file, header=0, names=["code", "date", "close", "max", "low", "avg", "changePerc", "volume", "turnover in BEST", "total turnover"])

def get_last_dates_for_firms(csv_file, json_file, output_json):
    csv_data = load_or_create_csv(csv_file)
    csv_data["date"] = pd.to_datetime(csv_data["date"], errors='coerce', format="%d.%m.%Y")
    csv_data = csv_data.sort_values(by=["code", "date"])

    with open(json_file, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    last_dates = []
    for firm in json_data:
        code = firm["name"]
        firm_data = csv_data[csv_data["code"] == code]

        if not firm_data.empty:
            last_date = firm_data["date"].max().strftime("%d.%m.%Y")
        else:
            date_10_years_ago = (datetime.today() - relativedelta(years=10)).strftime("%d.%m.%Y")
            last_date = date_10_years_ago

        last_dates.append({"code": code, "last_date": last_date})

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(last_dates, file, ensure_ascii=False, indent=4)
    print(f"Last dates saved to {output_json}.")

def outdated_firms(last_dates_json):
    with open(last_dates_json, "r", encoding="utf-8") as file:
        last_dates_data = json.load(file)

    today = datetime.today().strftime("%d.%m.%Y")
    for entry in last_dates_data:
        code = entry["code"]
        last_date = entry["last_date"]

        if last_date and last_date != today:
            print(f"Code: {code}, Last Date: {last_date}, Today's Date: {today}")
            Call_save_data_from_to(code, last_date, today)

def Call_Filter_II():
    get_last_dates_for_firms(csv_file_path, json_file_path, output_json)
    outdated_firms(output_json)

def format_price(price):
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fetch_data_for_period(firm_code, start_date, end_date):
    session = requests.Session()
    payload = {"FromDate": start_date, "ToDate": end_date, "Code": firm_code}
    response = session.post(url, data=payload)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if table:
            rows = []
            headers = [th.text.strip() for th in table.find_all('th')]
            headers = ['date', "close", "max", "low", "avg", "changePerc", "volume", "turnover in BEST", "total turnover"]
            #print(len(headers))
            for tr in table.find_all('tr')[1:]:
                cells = [td.text.strip() for td in tr.find_all('td')]
                if cells:
                    rows.append(cells)
            data = pd.DataFrame(rows, columns=headers)
            data.insert(0, "Issuer", firm_code)
            return data
    return None

def fetch_data_for_large_date_range(firm_code, start_date, end_date):
    all_data = []
    max_days = 365
    current_start = datetime.strptime(start_date, "%d.%m.%Y")

    date_intervals = []
    while current_start <= datetime.strptime(end_date, "%d.%m.%Y"):
        next_end = min(current_start + timedelta(days=max_days - 1), datetime.strptime(end_date, "%d.%m.%Y"))
        date_intervals.append((current_start.strftime("%d.%m.%Y"), next_end.strftime("%d.%m.%Y")))
        current_start = next_end + timedelta(days=1)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_data_for_period, firm_code, start, end): (start, end) for start, end in date_intervals}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                all_data.append(result)

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def Call_save_data_from_to(firm_code, start_date, end_date):
    try:
        data = fetch_data_for_large_date_range(firm_code, start_date, end_date)
        if data is not None:
            for column in ["close", "max", "low", "avg", "turnover in BEST", "total turnover"]:
                if column in data.columns:
                    data[column] = data[column].apply(lambda x: ReplaceDots(x))
            #print(data)
            data.drop_duplicates(subset=['Issuer', 'date'], inplace=True)

            data.to_csv(pat, mode='a', header=False, index=False)
            print(f"Data for {firm_code} saved.")
    except BrokenPipeError as e:
        print(f"BrokenPipeError while processing {firm_code}: {e}")
    except Exception as e:
        print(f"Unexpected error while processing {firm_code}: {e}")


# def Call_save_data_from_to(firm_code, start_date, end_date):
#     data = fetch_data_for_large_date_range(firm_code, start_date, end_date)
#     if data is not None:
#         for column in ["close", "max", "low", "avg"]:
#             if column in data.columns:
#                 data[column] = data[column].apply(lambda x: format_price(float(x.replace(',', '.'))))
#         data.to_csv(pat, mode='a', header=False, index=False, encoding="utf-8")
#         print(f"Data for {firm_code} saved.")
#

def ReplaceDots(price_string):
    price_string = price_string.replace(".", "'")
    price_string = price_string.replace(",", ".")
    price_string = price_string.replace("'", ",")
    return price_string


Call_Filter_1()
fachNames()
end_time = time.time()
duration = end_time - start_time
print(f"Program completed in {duration:.2f} seconds")
import sys
sys.exit(0)