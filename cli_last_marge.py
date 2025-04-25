from tkinter import filedialog
import pandas as pd
from tqdm import tqdm
import sqlite3
import time

# py cli_last_marge.py

file_old = ".\data\old_utc.xlsx"
dist_excel = pd.read_excel(io=file_old, sheet_name="Лист1")

total_count = len(dist_excel["ID"])
print("total_count:", total_count)
print("cols:", dist_excel.keys())

conn = sqlite3.connect("./db/index.db")
cursor = conn.cursor()

# input("Ожидаю подтверждения...")

for i in tqdm(range(total_count)):
    id_number = dist_excel["ID"][i]
    translate_name = dist_excel["город"][i]

    # print(f"data [{i}]: [{translate_name}, {id_number}]")

    data = cursor.execute(
        "UPDATE dataCity SET city_old_ai = ? WHERE id = ?;",
        [str(translate_name), int(id_number)],
    ).fetchall()

    # data = cursor.execute(
    #     "SELECT id, city_old_ai FROM dataCity WHERE id = ?;",
    #     [int(id_number)],
    # ).fetchall()

    # try:
    #     data = cursor.execute(
    #         "UPDATE data SET city_old_ai = ? WHERE id = ?;",
    #         [translate_name, id_number],
    #     ).fetchall()
    # except:
    #     print(f"error [{i}]: ...")

    # print(f"data [{i}]: [{translate_name}, {id_number}, [{data}]]")

    # time.sleep(0.5)

    if (i % 100) == 0:
        conn.commit()
        time.sleep(1)

conn.commit()
conn.close()

print("++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++ РАБОТА ЗАВЕРШЕНА ++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++")
