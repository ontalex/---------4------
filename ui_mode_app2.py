import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from deep_translator import GoogleTranslator
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pandas as pd
from datetime import datetime
import pytz
import threading
from queue import Queue
import random


class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработчик географических данных")
        self.root.geometry("900x650")

        # Параметры программы
        self.source_file = tk.StringVar()
        self.save_file = tk.StringVar()
        self.columns_to_translate = tk.StringVar(value="city,country")
        self.add_timezone = tk.BooleanVar(value=False)
        self.timezone_column = tk.StringVar(value="timezone")
        self.threads_count = tk.IntVar(value=4)
        self.limit_rows = tk.BooleanVar(value=False)
        self.start_row = tk.IntVar(value=0)
        self.end_row = tk.IntVar(value=100)

        # Создание интерфейса
        self.create_widgets()

        # Очереди для многопоточной работы
        self.timezone_queue = Queue()
        self.translate_queue = Queue()
        self.result_queue = Queue()

        # Флаги управления
        self.processing = False
        self.cancel_flag = False

    def create_widgets(self):
        # Блок работы с файлами
        file_frame = ttk.LabelFrame(self.root, text="Файловая система", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(file_frame, text="Исходные данные:").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Entry(file_frame, textvariable=self.source_file, width=50).grid(
            row=0, column=1
        )
        ttk.Button(file_frame, text="Выбрать...", command=self.browse_source).grid(
            row=0, column=2
        )

        ttk.Label(file_frame, text="Результат:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.save_file, width=50).grid(
            row=1, column=1
        )
        ttk.Button(file_frame, text="Выбрать...", command=self.browse_save).grid(
            row=1, column=2
        )

        # Блок параметров обработки
        process_frame = ttk.LabelFrame(
            self.root, text="Настройки обработки", padding=10
        )
        process_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(process_frame, text="Поля для перевода (через запятую):").grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Entry(process_frame, textvariable=self.columns_to_translate, width=50).grid(
            row=0, column=1
        )

        ttk.Checkbutton(
            process_frame,
            text="Добавить информацию о часовом поясе",
            variable=self.add_timezone,
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W)

        ttk.Label(process_frame, text="Название колонки для часового пояса:").grid(
            row=2, column=0, sticky=tk.W
        )
        ttk.Entry(process_frame, textvariable=self.timezone_column, width=20).grid(
            row=2, column=1, sticky=tk.W
        )

        ttk.Label(process_frame, text="Число потоков:").grid(
            row=3, column=0, sticky=tk.W
        )
        ttk.Spinbox(
            process_frame, from_=1, to=16, textvariable=self.threads_count, width=5
        ).grid(row=3, column=1, sticky=tk.W)

        # Блок ограничений
        limit_frame = ttk.LabelFrame(self.root, text="Ограничения выборки", padding=10)
        limit_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Checkbutton(
            limit_frame,
            text="Ограничить число обрабатываемых записей",
            variable=self.limit_rows,
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W)

        ttk.Label(limit_frame, text="Начальная запись:").grid(
            row=1, column=0, sticky=tk.W
        )
        ttk.Spinbox(
            limit_frame, from_=0, to=100000, textvariable=self.start_row, width=10
        ).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(limit_frame, text="Конечная запись:").grid(
            row=1, column=2, sticky=tk.W
        )
        ttk.Spinbox(
            limit_frame, from_=0, to=100000, textvariable=self.end_row, width=10
        ).grid(row=1, column=3, sticky=tk.W)

        # Блок управления
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_button = ttk.Button(
            control_frame, text="Запустить обработку", command=self.start_processing
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(
            control_frame,
            text="Прервать",
            command=self.cancel_processing,
            state=tk.DISABLED,
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Блок прогресса
        progress_frame = ttk.LabelFrame(
            self.root, text="Ход выполнения (общее количество операций)", padding=10
        )
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.overall_progress = ttk.Progressbar(
            progress_frame, orient=tk.HORIZONTAL, mode="determinate"
        )
        self.overall_progress.pack(fill=tk.X, pady=5)

        self.current_task_label = ttk.Label(progress_frame, text="Ожидание запуска...")
        self.current_task_label.pack(fill=tk.X)

        self.details_label = ttk.Label(progress_frame, text="")
        self.details_label.pack(fill=tk.X)

        # Журнал событий
        self.log_text = tk.Text(progress_frame, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(progress_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_source(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Файлы Excel", "*.xlsx *.xls"), ("Все файлы", "*.*")]
        )
        if filename:
            self.source_file.set(filename)
            try:
                df = pd.read_excel(filename)
                self.end_row.set(len(df) - 1)
                self.log_message(f"Данные загружены. Общее число записей: {len(df)}")
            except Exception as e:
                self.log_message(f"Ошибка чтения файла: {str(e)}")

    def browse_save(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Файлы Excel", "*.xlsx"), ("Все файлы", "*.*")],
        )
        if filename:
            self.save_file.set(filename)

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_processing(self):
        if not self.source_file.get() or not self.save_file.get():
            messagebox.showerror(
                "Ошибка",
                "Необходимо указать исходный файл и файл для сохранения результатов",
            )
            return

        if self.limit_rows.get() and self.start_row.get() > self.end_row.get():
            messagebox.showerror(
                "Ошибка", "Начальная позиция не может превышать конечную"
            )
            return

        self.processing = True
        self.cancel_flag = False
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.log_message("=== Начало обработки данных ===")

        processing_thread = threading.Thread(target=self.run_processing)
        processing_thread.start()

        self.update_progress()

    def cancel_processing(self):
        self.cancel_flag = True
        self.log_message("=== Обработка прервана пользователем ===")
        self.cancel_button.config(state=tk.DISABLED)

    def run_processing(self):
        try:
            # Инициализация сервисов
            geolocator = Nominatim(user_agent="OpenStreetMap")
            timeFinder = TimezoneFinder()

            # Чтение данных
            self.log_message("Загрузка исходных данных...")
            source_data = pd.read_excel(self.source_file.get())

            # Определение диапазона
            if self.limit_rows.get():
                start = max(0, self.start_row.get())
                end = min(len(source_data) - 1, self.end_row.get())
                source_data = source_data.iloc[start : end + 1]
                self.log_message(
                    f"Обработка записей с {start} по {end} (всего {end-start+1} записей)"
                )
            else:
                self.log_message(
                    f"Обработка всех записей (всего {len(source_data)} записей)"
                )

            # Добавление колонки для часового пояса
            if self.add_timezone.get():
                timezone_col = self.timezone_column.get()
                source_data[timezone_col] = [""] * len(source_data)

            data_dict = source_data.to_dict()
            total_records = len(source_data)

            # Запуск потоков обработки
            self.log_message(f"Активация {self.threads_count.get()} рабочих потоков...")

            # Потоки для часовых поясов
            timezone_threads = []
            for _ in range(self.threads_count.get()):
                t = threading.Thread(
                    target=self.process_timezone_worker, args=(timeFinder, geolocator)
                )
                t.start()
                timezone_threads.append(t)

            # Потоки для перевода
            translate_threads = []
            columns = [
                col.strip() for col in self.columns_to_translate.get().split(",")
            ]
            for col in columns:
                for _ in range(self.threads_count.get()):
                    t = threading.Thread(
                        target=self.process_translate_worker, args=(col,)
                    )
                    t.start()
                    translate_threads.append(t)

            # Добавление задач в очередь
            self.log_message("Постановка задач в очередь обработки...")

            # Для часовых поясов
            if self.add_timezone.get():
                for i in range(total_records):
                    if self.cancel_flag:
                        break
                    self.timezone_queue.put(
                        (i, data_dict["lat"][i], data_dict["lng"][i])
                    )

            # Для перевода
            for col in columns:
                for i in range(total_records):
                    if self.cancel_flag:
                        break
                    self.translate_queue.put((i, data_dict[col][i]))

            # Обработка результатов
            self.log_message("Сбор и обработка результатов...")
            processed = 0
            total_tasks = total_records * (1 + len(columns))

            while processed < total_tasks:
                if self.cancel_flag:
                    break

                result = self.result_queue.get()
                if result[0] == "timezone":
                    _, i, offset = result
                    data_dict[self.timezone_column.get()][i] = offset
                elif result[0] == "translate":
                    _, col, i, translated = result
                    data_dict[col][i] = self.modify_translation(
                        translated, data_dict[col][i]
                    )

                processed += 1
                self.update_progress(processed, total_tasks)
                self.result_queue.task_done()

            if self.cancel_flag:
                self.log_message("=== Процесс остановлен ===")
                return

            # Завершение работы потоков
            for _ in range(self.threads_count.get()):
                self.timezone_queue.put(None)
                for col in columns:
                    self.translate_queue.put(None)

            for t in timezone_threads + translate_threads:
                t.join()

            # Сохранение результатов
            self.log_message("Экспорт результатов...")
            result_df = pd.DataFrame(data_dict)
            print(columns)
            result_df.to_excel(self.save_file.get())

            self.log_message("=== Обработка успешно завершена ===")

        except Exception as e:
            self.log_message(f"Критическая ошибка: {str(e)}")
        finally:
            self.processing = False
            self.root.after(0, self.finish_processing)

    def modify_translation(self, translated, original):
        """Модификация перевода для обеспечения отличий от оригинала"""
        return translated

    def update_progress(self, processed, total):
        """Обновление информации о прогрессе"""
        progress_percent = (processed / total) * 100
        self.overall_progress["value"] = progress_percent
        self.current_task_label.config(
            text=f"Выполнено: {processed} из {total} ({progress_percent:.1f}%)"
        )
        self.root.update_idletasks()

    def finish_processing(self):
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.overall_progress["value"] = 0
        self.current_task_label.config(text="Процесс завершен")

    def process_timezone_worker(self, timeFinder, geolocator):
        while True:
            item = self.timezone_queue.get()
            if item is None:
                break

            i, lat, lng = item
            try:
                timezone = timeFinder.timezone_at(lat=lat, lng=lng)
                tz = pytz.timezone(timezone)
                offset_hours = datetime.now(tz).utcoffset().total_seconds() / 3600
                self.log_message(f"Часовой пояс для записи {i}: {offset_hours}")
                self.result_queue.put(("timezone", i, offset_hours))
            except Exception as e:
                self.log_message(
                    f"Ошибка определения часового пояса для записи {i}: {e}"
                )
                self.result_queue.put(("timezone", i, None))
            finally:
                self.timezone_queue.task_done()

    def process_translate_worker(self, col_name):
        count_tries = 0
        max_count_tries = 16
        is_done = False
        while (count_tries != max_count_tries) or is_done == False:
            item = self.translate_queue.get()
            if item is None:
                break

            i, text = item
            try:
                translated = GoogleTranslator(source="auto", target="ru").translate(
                    text=str(text)
                )
                print((translated, str(text)))
                self.result_queue.put(("translate", col_name, i, translated))

                is_done = True

                if str(translated) == str(text):
                    is_done = False
                    self.log_message(
                        f"Ошибка перевода для записи {i}, поле {col_name}, попытка {count_tries}: неверный перевод"
                    )
                    continue

                self.translate_queue.task_done()
            except Exception as e:
                self.log_message(
                    f"Ошибка перевода для записи {i}, поле {col_name}, попытка {count_tries}: {e}"
                )
                count_tries = count_tries + 1
                self.result_queue.put(("translate", col_name, i, None))

                if (count_tries > max_count_tries) or is_done == True:
                    self.translate_queue.task_done()
            finally:
                print("_")


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()
