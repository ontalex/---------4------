from tkinter import filedialog
import pandas as pd
from tqdm import tqdm
import sqlite3
import time

# py cli_to_excel.py

conn = sqlite3.connect("./db/index.db")
cursor = conn.cursor()
table_out = cursor.execute("SELECT * FROM ToExcel;").fetchall()
print("table_out:", table_out)

len_table_out = len(table_out)

columns = [
    "id",
    "country",
    "city",
    "city_ascii",
    "lat",
    "lng",
    "admin_name",
    "iso2",
    "iso3",
    "capital",
    "timezone",
    "population",
]

file_out = "./data/new_utc.xlsx"
df = pd.DataFrame(columns=columns)
df_dict = df.to_dict()
print("df_dict:", df_dict)

for i_row in tqdm(range(len_table_out), colour="GREEN"):
    for i_column in range(len(columns)):
        df_dict[columns[i_column]][i_row] = table_out[i_row][i_column]

print("new dict:", df_dict)

pd.DataFrame(data=df_dict).to_excel(file_out, "Sheet1")
