# py cli_past.py
import sqlite3
import pandas as pd
from tqdm import tqdm
import time
from deep_translator import GoogleTranslator


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
        or "Z:\worldcities.xlsx",
        "countries_sheet": input(
            "> Введите название листа со странами (по умолчанию TranslateCountries): "
        )
        or "TranslateCountries",
        "cities_sheet": input(
            "> Введите название листа с городами (по умолчанию TranslateCities): "
        )
        or "TranslateCities",
        "batch_size": int(
            input(
                "> Введите частоту пауз (количество строк между паузами, по умолчанию 50): "
            )
            or 50
        ),
        "max_retries": int(
            input(
                "> Введите количество попыток перевода при ошибке (по умолчанию 10): "
            )
            or 10
        ),
        "pause_duration": int(
            input("> Введите длительность паузы в секундах (по умолчанию 5): ") or 5
        ),
        "retry_pause": int(
            input(
                "> Введите длительность паузы при повторе перевода (по умолчанию 1): "
            )
            or 1
        ),
    }
    return params


def process_countries(db_cursor, df_dict, row_count):
    """Обработка данных стран"""
    if input("> Удалить текущие страны? (да/нет) = ").lower() == "да":
        db_cursor.execute("DELETE FROM country;")

    if input("> Добавить текущие страны? (да/нет) = ").lower() == "да":
        data = [
            (str(df_dict["origin"][i]), str(df_dict["translate"][i]))
            for i in range(row_count)
        ]
        db_cursor.executemany(
            "INSERT INTO country (name, trans_name) VALUES (?, ?)", data
        )


def translate_city_name(name, translator, max_retries, retry_pause):
    """Выполнение перевода с повторными попытками"""
    for attempt in range(max_retries + 1):
        try:
            translated = translator.translate(name)
            if translated.lower() == name.lower():
                return None  # Не сохраняем перевод если совпадает с оригиналом
            return translated
        except Exception as e:
            if attempt == max_retries:
                print(f"Ошибка перевода для '{name}': {str(e)}")
                return None
            time.sleep(retry_pause)


def process_cities(db_cursor, df_dict, row_count, params):
    """Обработка данных городов"""
    if input("> Удалить текущие города? (да/нет) = ").lower() == "да":
        db_cursor.execute("DELETE FROM city;")

    if input("> Выполнить перевод названий городов? (да/нет) = ").lower() == "да":
        translator = GoogleTranslator(target="ru", source="en")
        existing_cities = set(
            row[0] for row in db_cursor.execute("SELECT name FROM city;").fetchall()
        )

        start_translate = input(">> Начать с (0 по умолчанию): ") or 0
        end_translate = (
            input(f">> Закончить на ({row_count} по умолчанию): ") or row_count
        )

        start_translate = int(start_translate)
        end_translate = int(end_translate)

        for i in tqdm(range(start_translate, end_translate), desc="Перевод городов"):
            origin = str(df_dict["origin"][i])

            if origin in existing_cities:
                continue

            if i > 0 and i % params["batch_size"] == 0:
                print(f">> Пауза {params['pause_duration']} сек...")
                time.sleep(params["pause_duration"])

            translated = translate_city_name(
                origin, translator, params["max_retries"], params["retry_pause"]
            )

            if (i % 10) == 0:
                print(
                    f"[INFO] (i-{i}) insert for {origin} [{i}] - trans: {translated};"
                )

            try:
                db_cursor.execute(
                    "INSERT INTO city (name, trans_name) VALUES (?, ?)",
                    (origin, translated),
                )
            except:
                print(f"[ERROR] insert for {origin} [{i}] - trans: {translated};")


def main():
    params = get_user_input()

    # Чтение данных Excel
    countries_df = pd.read_excel(
        io=params["excel_path"], sheet_name=params["countries_sheet"]
    )
    print(f"Стран найдено: {len(countries_df)}")

    # Инициализация БД
    with sqlite3.connect("./db/index.db") as conn:
        cursor = conn.cursor()

        # Обработка стран
        process_countries(cursor, countries_df.to_dict(), len(countries_df))
        conn.commit()

        print("\n" + "=" * 50 + "\n")

        # Обработка городов
        cities_df = pd.read_excel(
            io=params["excel_path"], sheet_name=params["cities_sheet"]
        )
        print(f"Городов найдено: {len(cities_df)}")

        process_cities(cursor, cities_df.to_dict(), len(cities_df), params)
        conn.commit()

        print("++++++++++++++++++++++++++++++++++++++++++++")
        print("++++++++++ РАБОТА ЗАВЕРШЕНА ++++++++++++++++")
        print("++++++++++++++++++++++++++++++++++++++++++++")


if __name__ == "__main__":
    main()
