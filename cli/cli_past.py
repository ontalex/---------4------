# py cli_past.py

import sqlite3
import pandas as pd
import tqdm
import time
from deep_translator import GoogleTranslator

P_FILE_SOURCE = "F:\worldcities__2.xlsx"
P_SHEET_SOURCE_COUNTRIES = "TranslateCountries"
P_SHEET_SOURCE_CITIES = "TranslateCities"
COUNT_ROWS = 0

P_TAKE_COUNT = 50
P_COUNT_RESTART_TRANS = 10

# чтение таблицы
df = pd.read_excel(io=P_FILE_SOURCE, sheet_name=P_SHEET_SOURCE_COUNTRIES)
df_dict = df.to_dict()
COUNT_ROWS = len(df_dict["origin"])
print("Count:", COUNT_ROWS)

# Инициализация БД
db_connection = sqlite3.connect("./db/index.db")
db_cursor = db_connection.cursor()

if input("> Удалить текущие страны? (да\нет) = ") == "да":
    db_cursor.execute("DELETE FROM country;").fetchall()
    db_connection.commit()

# обработка данных excel
if input("> Добавить текущие страны? (да\нет) = ") == "да":
    for i in tqdm.tqdm(range(COUNT_ROWS)):
        blob = (df_dict["origin"][i], df_dict["translate"][i])
        req = db_cursor.execute(
            "INSERT INTO country (name, trans_name) VALUES (?, ?)", blob
        )
        res = req.fetchall()
    db_connection.commit()

print("\n\n\n ======================= \n\n\n")

df = pd.read_excel(io=P_FILE_SOURCE, sheet_name=P_SHEET_SOURCE_CITIES)
df_dict = df.to_dict()
COUNT_ROWS = len(df_dict["origin"])
print("Count:", COUNT_ROWS)

if input("> Удалить текущие города? (да\нет) = ") == "да":
    """"""
    db_cursor.execute("DELETE FROM city;").fetchall()
    db_connection.commit()

if input("> Выполнить перевод названий городов? (да\нет) = ") == "да":
    """"""
    for i in tqdm.tqdm(range(COUNT_ROWS)):

        origin_xlsx = df_dict["origin"][i]
        translate = df_dict["translate"][i]  # null

        if (i % P_TAKE_COUNT) == 0 and i > 0:
            print(">> ОСТАНОВКА НА ОЖИДАНИЕ (5 секунд) ...")
            time.sleep(5)

        # есть ли перевод уже в база данных
        already_has = db_cursor.execute(
            "SELECT * FROM city WHERE name = ?;", tuple([str(origin_xlsx)])
        ).fetchall()
        db_connection.commit()
        # print("already_has: ", already_has)

        if len(already_has) == 0 or already_has[1] != str(origin_xlsx).strip():
            transalte_gog = GoogleTranslator(target="ru").translate(str(origin_xlsx))
            blob = (str(origin_xlsx), str(transalte_gog))

            current_count = 0
            while current_count <= P_COUNT_RESTART_TRANS and str(origin_xlsx) == str(
                transalte_gog
            ):
                print("Blob:", blob)
                print(">> ОСТАНОВКА НА ОЖИДАНИЕ (5 секунд) ...")
                time.sleep(1)
                transalte_gog = GoogleTranslator(target="ru").translate(
                    str(origin_xlsx)
                )
                blob = (str(origin_xlsx), str(transalte_gog))
                current_count = current_count + 1

            print("Blob:", blob)
            db_cursor.execute(
                "INSERT INTO city (name, trans_name) VALUES (?, ?);", blob
            ).fetchall()
            db_connection.commit()


db_connection.close()
