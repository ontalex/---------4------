import time
from tkinter import filedialog
from tqdm import tqdm
import pandas as pd
import sqlite3

# cli_last_marge.py

file_excel_out = "Z:\worldcities_out.xlsx"
dist_excel = pd.read_excel(io=file_excel, sheet_name="Sheet1").to_dict()

total_count = len(dist_excel["id"])
print("total_count:", total_count)

conn = sqlite3.connect("./db/index.db")
cursor = conn.cursor()

for i in tqdm(range(total_count)):
    id_number = dist_excel["id"][i]
    str_city = dist_excel["city"][i]

    # print(f"{i}) {id_number}; {id_city}")

    cursor.execute(
        "UPDATE data SET city.city = ? WHERE city.id = ?;", [str_city, id_number]
    ).fetchall()

    if (i % 100) == 0:
        conn.commit()

conn.commit()
conn.close()

print("++++++++++++++++++++++++++++++++++++++++++++")
print("++++++++++ РАБОТА ЗАВЕРШЕНА ++++++++++++++++")
print("++++++++++++++++++++++++++++++++++++++++++++")
