import sqlite3
from tkinter import filedialog
from tqdm import tqdm

# py cli_find_no_translate.py


def get_user_input():
    """Получение параметров от пользователя"""
    params = {
        "excel_path": input(
            "> Введите полный путь к файлу Excel (например, Z:\worldcities.xlsx) (лучше поместить файл в корень диска): "
        )
        or "Z:\worldcities.xlsx",
        "db_path": input(
            "> Введите полный путь к файлу базы данных (лучше поместить файл в корень диска): "
        )
        or "Z:\Практика-4-весна\db\index.db",
        "join_symbol": input(
            "> Введите символы через которые будут соединены оригиналы "
        ),
        "start": input("> начать с ") or 0,
        "end": input("> взять ") or 100,
    }
    return params


def main():
    user_input = get_user_input()
    filedirection = filedialog.askdirectory(title="Куда сохранить данные?")

    current = 0
    len_data = len(cursor.execute(
                "select city.name from city where (city.trans_name is NULL);",
            ).fetchall())

    with sqlite3.connect(".\db\index.db") as conn:
        cursor = conn.cursor()

        path = "".join([filedirection, f"/exit-{user_input["start"]}-{user_input["end"]}.txt"])
        with open(file=path, encoding="utf-8", mode="w+") as file:
            print("Count lines:", file)
            data = cursor.execute(
                "select city.name from city where (city.trans_name is NULL) LIMIT ? OFFSET ?;",
                (user_input["end"], user_input["start"]),
            ).fetchall()
            print("data:", data)

            for i in tqdm(range(len(data)), "Добавление в файл"):
                file.write(data[i][0] + user_input["join_symbol"])
                print("data:", data[i][0])


if __name__ == "__main__":
    main()
