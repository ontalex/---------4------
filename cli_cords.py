import sqlite3
import geopy
import pytz
from tqdm import tqdm
from datetime import datetime

# py cli_cords.py

from timezonefinder import TimezoneFinder
import pytz
from datetime import datetime


def get_utc_offset(lat: float, lng: float) -> float:
    """
    Возвращает смещение от UTC в часах для заданных координат.
    Учитывает текущее время (летнее/зимнее время).
    """
    # Инициализация TimezoneFinder
    tf = TimezoneFinder()

    # Получаем название временной зоны (например, 'Europe/Moscow')
    timezone_str = tf.timezone_at(lat=lat, lng=lng)

    if not timezone_str:
        raise ValueError("Временная зона не найдена для данных координат")

    # Получаем объект временной зоны
    tz = pytz.timezone(timezone_str)

    # Вычисляем текущее смещение от UTC
    now = datetime.now(tz)
    offset_seconds = now.utcoffset().total_seconds()
    offset_hours = offset_seconds / 3600  # Преобразуем секунды в часы

    return offset_hours


conn = sqlite3.connect("./db/index.db")
cursor = conn.cursor()
db_data = cursor.execute("select data.id, data.lat, data.lng from data;").fetchall()
db_data_len = len(db_data)
print("Len:", db_data_len)
# print("Data:", db_data[1])

for i in tqdm(range(db_data_len)):
    # for i in tqdm(range(0, 100)):

    offset = get_utc_offset(db_data[i][1], db_data[i][2])
    # print((id, lat, lng, offset))

    print("Data:", db_data[i][0], "-", db_data[i][1], "-", db_data[i][2], "-", offset)

    cursor.execute(
        "UPDATE data SET timezone = ? WHERE data.id = ?;",
        (float(offset), int(db_data[i][0])),
    ).fetchall()

conn.commit()
conn.close()
