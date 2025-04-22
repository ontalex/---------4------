import time
from tkinter import filedialog
from tqdm import tqdm
import pandas as pd
import sqlite3

# py cli_recap.py

# Воссаждать данные из таблицы

file_excel = "Z:\worldcities.xlsx"
dist_excel = pd.read_excel(io=file_excel, sheet_name="Sheet1").to_dict()

# print(dist_excel)

total_count = len(dist_excel["id"])
print("total_count:", total_count)

conn = sqlite3.connect("./db/index.db")
cursor = conn.cursor()

for i in tqdm(range(total_count)):
    city_name_dist = str(dist_excel["city_ascii"][i]).replace(" -", "-", -1)
    country_name_dist = str(dist_excel["country"][i]).replace(" -", "-", -1)

    id = dist_excel["id"][i]
    lat = dist_excel["lat"][i]
    lng = dist_excel["lng"][i]
    iso2 = dist_excel["iso2"][i]
    iso3 = dist_excel["iso3"][i]
    admin_name = dist_excel["admin_name"][i]
    capital = dist_excel["capital"][i]
    population = dist_excel["population"][i]

    db_city = cursor.execute(
        "select * from city where city.name like ?;", [f"{city_name_dist}"]
    ).fetchone()
    # print("DB City:", db_city)

    db_country = cursor.execute(
        "select * from country where country.name like ?;", [f"{country_name_dist}"]
    ).fetchone()
    # print("DB Country:", db_country)

    # print(
    #     "data:",
    #     (
    #         db_city[0],
    #         city_name_dist,
    #         db_country[0],
    #         lat,
    #         lng,
    #         iso2,
    #         iso3,
    #         admin_name,
    #         capital,
    #         population,
    #     ),
    # )

    cursor.execute(
        "INSERT INTO data (id, city_id, city_ascii, country_id, lat, lng, iso2, iso3, admin_name, capital, population) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
        (
            id,
            db_city[0],
            city_name_dist,
            db_country[0],
            lat,
            lng,
            iso2,
            iso3,
            admin_name,
            capital,
            population,
        ),
    ).fetchone()
    # time.sleep(0.01)
    conn.commit()

conn.close()

print("++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++ РАБОТА ЗАВЕРШЕНА ++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++")
