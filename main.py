import tkinter as tk
from tkinter import ttk
from PIL import ImageGrab
from paddleocr import PaddleOCR
import pyperclip
import numpy as np
import json
import os
import requests

class ScreenshotApp:
    def __init__(self, root, index):
        self.root = root
        self.index = index
        self.root.title(f"Screenshot App {self.index}")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", "white")

        self.canvas = tk.Canvas(root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Загрузка сохраненных данных
        self.load_settings()

        # Начальный размер рамки
        self.rect = self.canvas.create_rectangle(self.rect_coords[0], self.rect_coords[1], self.rect_coords[2], self.rect_coords[3], outline='grey', width=12)

        self.move_symbol = self.canvas.create_text(self.rect_coords[2], self.rect_coords[1] - 30, text="•", fill="grey", font=("Calibri", 48))

        self.screenshot_button = ttk.Button(root, text="Скриншот", command=self.take_screenshot)
        self.screenshot_button_window = self.canvas.create_window(self.rect_coords[0], self.rect_coords[1] - 30, window=self.screenshot_button, anchor='nw')

        self.copy_button = ttk.Button(root, text="Скопировать текст", command=self.copy_to_clipboard, state=tk.DISABLED)
        self.copy_button_window = self.canvas.create_window(self.rect_coords[0] + 80, self.rect_coords[1] - 30, window=self.copy_button, anchor='nw')

        self.exit_button = ttk.Button(root, text="Выход", command=self.exit_app)
        self.exit_button_window = self.canvas.create_window(self.rect_coords[0] + 197, self.rect_coords[1] - 30, window=self.exit_button, anchor='nw')

        self.hide_button = ttk.Button(root, text="Скрыть", command=self.toggle_visibility)
        self.hide_button_window = self.canvas.create_window(self.rect_coords[0] + 280, self.rect_coords[1] - 30, window=self.hide_button, anchor='nw')

        self.up_button = ttk.Button(root, text="Вверх", command=self.show_previous_translation)
        self.down_button = ttk.Button(root, text="Вниз", command=self.show_next_translation)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.start_x = None
        self.start_y = None
        self.resize_corner = None
        self.moving = False
        self.hidden = False
        self.translations = []
        self.current_translation_index = 0

        # Инициализация PaddleOCR
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

    def load_settings(self):
        settings_file = f"settings_{self.index}.json"
        if os.path.exists(settings_file):
            with open(settings_file, "r") as file:
                settings = json.load(file)
                self.rect_coords = settings.get("rect_coords", [100, 150, 645, 326])
                self.window_position = settings.get("window_position", [100 + (self.index - 1) * 50, 100])
        else:
            self.rect_coords = [100, 150, 645, 326]
            self.window_position = [100 + (self.index - 1) * 50, 100]

        # Устанавливаем позицию окна
        self.root.geometry(f"+{self.window_position[0]}+{self.window_position[1]}")

    def save_settings(self):
        settings = {
            "rect_coords": self.canvas.coords(self.rect),
            "window_position": [self.root.winfo_x(), self.root.winfo_y()]
        }
        settings_file = f"settings_{self.index}.json"
        with open(settings_file, "w") as file:
            json.dump(settings, file)

    def exit_app(self):
        # Сохранение настроек текущего окна
        settings = {
            "rect_coords": self.canvas.coords(self.rect),
            "window_position": [self.root.winfo_x(), self.root.winfo_y()]
        }
        settings_file = f"settings_{self.index}.json"
        with open(settings_file, "w") as file:
            json.dump(settings, file)

        # Сохранение настроек другого окна
        if hasattr(self, 'other_app'):
            other_settings = {
                "rect_coords": self.other_app.canvas.coords(self.other_app.rect),
                "window_position": [self.other_app.root.winfo_x(), self.other_app.root.winfo_y()]
            }
            other_settings_file = f"settings_{self.other_app.index}.json"
            with open(other_settings_file, "w") as file:
                json.dump(other_settings, file)

        # Закрытие обоих окон
        if hasattr(self, 'other_app'):
            self.other_app.root.destroy()
        self.root.destroy()

    def toggle_visibility(self):
        if not self.hidden:
            # Скрытие всех кнопок и текста
            self.canvas.itemconfigure(self.screenshot_button_window, state='hidden')
            self.canvas.itemconfigure(self.copy_button_window, state='hidden')
            self.canvas.itemconfigure(self.exit_button_window, state='hidden')
            if hasattr(self, 'up_button_window'):
                self.canvas.itemconfigure(self.up_button_window, state='hidden')
            if hasattr(self, 'down_button_window'):
                self.canvas.itemconfigure(self.down_button_window, state='hidden')
            if hasattr(self, 'translated_textbox'):
                self.translated_textbox.place_forget()
            self.canvas.itemconfigure(self.rect, state='hidden')
            self.hide_button.config(text="Показать")
        else:
            # Показ всех кнопок и текста
            self.canvas.itemconfigure(self.screenshot_button_window, state='normal')
            self.canvas.itemconfigure(self.copy_button_window, state='normal')
            self.canvas.itemconfigure(self.exit_button_window, state='normal')
            if hasattr(self, 'up_button_window'):
                self.canvas.itemconfigure(self.up_button_window, state='normal')
            if hasattr(self, 'down_button_window'):
                self.canvas.itemconfigure(self.down_button_window, state='normal')
            if hasattr(self, 'translated_textbox'):
                coords = self.canvas.coords(self.rect)
                self.translated_textbox.place(
                    x=coords[0], y=coords[3] + 10, width=coords[2] - coords[0]
                )
            self.canvas.itemconfigure(self.rect, state='normal')
            self.hide_button.config(text="Скрыть")
        self.hidden = not self.hidden

    def on_button_press(self, event):
        x, y = event.x, event.y
        coords = self.canvas.coords(self.move_symbol)
        if coords[0] - 10 <= x <= coords[0] + 10 and coords[1] - 10 <= y <= coords[1] + 10:
            self.start_x = x
            self.start_y = y
            self.moving = True
        else:
            self.resize_corner = self.get_resize_corner(event.x, event.y)

    def on_move_press(self, event):
        cur_x = event.x
        cur_y = event.y
        if self.moving:
            self.move_rectangle(cur_x, cur_y)
        elif self.resize_corner:
            self.resize_rectangle(cur_x, cur_y)

    def on_button_release(self, event):
        self.resize_corner = None
        if self.moving:
            self.moving = False

    def get_resize_corner(self, x, y):
        coords = self.canvas.coords(self.rect)
        x1, y1, x2, y2 = coords
        if abs(x - x1) < 10 and abs(y - y1) < 10:
            return 'nw'
        elif abs(x - x2) < 10 and abs(y - y1) < 10:
            return 'ne'
        elif abs(x - x1) < 10 and abs(y - y2) < 10:
            return 'sw'
        elif abs(x - x2) < 10 and abs(y - y2) < 10:
            return 'se'
        elif abs(x - x1) < 10:
            return 'w'
        elif abs(x - x2) < 10:
            return 'e'
        elif abs(y - y1) < 10:
            return 'n'
        elif abs(y - y2) < 10:
            return 's'
        else:
            return None

    def resize_rectangle(self, x, y):
        coords = self.canvas.coords(self.rect)
        x1, y1, x2, y2 = coords
        if self.resize_corner == 'nw':
            x1, y1 = x, y
        elif self.resize_corner == 'ne':
            x2, y1 = x, y
        elif self.resize_corner == 'sw':
            x1, y2 = x, y
        elif self.resize_corner == 'se':
            x2, y2 = x, y
        elif self.resize_corner == 'w':
            x1 = x
        elif self.resize_corner == 'e':
            x2 = x
        elif self.resize_corner == 'n':
            y1 = y
        elif self.resize_corner == 's':
            y2 = y
        self.canvas.coords(self.rect, x1, y1, x2, y2)
        self.update_text_and_button_positions(x1, y1, x2, y2)

    def move_rectangle(self, x, y):
        dx = x - self.start_x
        dy = y - self.start_y
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.move_symbol, dx, dy)
        self.canvas.move(self.screenshot_button_window, dx, dy)
        self.canvas.move(self.copy_button_window, dx, dy)
        self.canvas.move(self.exit_button_window, dx, dy)
        self.canvas.move(self.hide_button_window, dx, dy)
        self.start_x = x
        self.start_y = y
        self.update_text_and_button_positions(self.canvas.coords(self.rect)[0] + dx, self.canvas.coords(self.rect)[1] + dy, self.canvas.coords(self.rect)[2] + dx, self.canvas.coords(self.rect)[3] + dy)

    def update_text_and_button_positions(self, x1, y1, x2, y2):
        if hasattr(self, 'translated_textbox'):
            self.translated_textbox.place(x=x1, y=y2 + 10, width=x2-x1)
        self.canvas.coords(self.move_symbol, x2, y1 - 30)
        self.canvas.coords(self.screenshot_button_window, x1, y1 - 30)
        self.canvas.coords(self.copy_button_window, x1 + 80, y1 - 30)
        self.canvas.coords(self.exit_button_window, x1 + 197, y1 - 30)
        self.canvas.coords(self.hide_button_window, x1 + 280, y1 - 30)
        if hasattr(self, 'up_button_window'):
            self.canvas.coords(self.up_button_window, x1 - 20, y2 + 10)
        if hasattr(self, 'down_button_window'):
            self.canvas.coords(self.down_button_window, x1 - 20, y2 + 40)

    def take_screenshot(self):
        self.root.attributes("-alpha", 0.0)  # Скрыть окно перед скриншотом
        self.root.update_idletasks()

        x1, y1, x2, y2 = self.canvas.coords(self.rect)
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))  # Смещение для исключения рамки

        # Сохраняем скриншот в памяти
        self.screenshot_image = screenshot

        self.root.attributes("-alpha", 0.3)  # Вернуть прозрачность
        self.recognize_and_translate_text()

    def recognize_and_translate_text(self):
        # Преобразуем изображение в формат, поддерживаемый PaddleOCR
        image_np = np.array(self.screenshot_image)

        # Распознавание текста с использованием PaddleOCR
        result = self.ocr.ocr(image_np, cls=True)
        text = ' '.join([line[1][0] for line in result[0]])

        if not text.strip():
            self.show_error("No text found in the image.")
            return
        self.text = text
        # Перевод текста с использованием Google Translate
        translate_url = "http://127.0.0.1:5000/translate"

        # Параметры запроса
        params = {
            "q": text,
            "source": "en",
            "target": "ru",
            "format": "text",
            "alternatives": 3
        }

        try:
            # Отправка POST-запроса к локальному серверу
            response = requests.post(translate_url, data=params)
            response.raise_for_status()  # Проверка на ошибки HTTP

            # Получение переведенного текста из ответа
            self.translations = response.json().get("alternatives")
            self.current_translation_index = 0

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при выполнении запроса: {e}")
            return None

        # Отображение переведенного текста
        self.show_text(self.translations[self.current_translation_index])
        self.copy_button.config(state=tk.NORMAL)

    def show_text(self, translated_text):
        # Удаление предыдущих текстов и кнопок, если они существуют
        if hasattr(self, 'translated_textbox'):
            self.translated_textbox.destroy()
            self.up_button.destroy()
            self.down_button.destroy()

        coords = self.canvas.coords(self.rect)
        x1, y1, x2, y2 = coords

        # Отображение переведенного текста
        self.translated_textbox = tk.Label(self.root, text=f"{self.current_translation_index + 1}/{len(self.translations)}: {translated_text}", font=("Times New Roman", 28), bg="gray", fg="black", wraplength=x2-x1, justify=tk.LEFT, anchor='nw')
        self.translated_textbox.place(x=x1, y=y2 + 10)

        # Создание кнопок "Вверх" и "Вниз"
        self.up_button = ttk.Button(self.root, text="↑", command=self.show_previous_translation, width=1)
        self.down_button = ttk.Button(self.root, text="↓", command=self.show_next_translation, width=1)
        self.up_button_window = self.canvas.create_window(x1-20, y2 + 10, window=self.up_button, anchor='nw')
        self.down_button_window = self.canvas.create_window(x1-20, y2 + 40, window=self.down_button, anchor='nw')

    def show_previous_translation(self):
        if self.current_translation_index > 0:
            self.current_translation_index -= 1
            self.show_text(self.translations[self.current_translation_index])

    def show_next_translation(self):
        if self.current_translation_index < len(self.translations) - 1:
            self.current_translation_index += 1
            self.show_text(self.translations[self.current_translation_index])

    def copy_to_clipboard(self):
        if hasattr(self, 'translated_textbox'):
            text = self.text
            pyperclip.copy(text)
            self.copy_button.config(text="✔ Copied")
            self.root.after(2000, lambda: self.copy_button.config(text="Copy Text"))

    def show_error(self, message):
        error_label = ttk.Label(self.root, text=message, foreground="red")
        error_label.pack(pady=10)

if __name__ == "__main__":
    root1 = tk.Tk()
    app1 = ScreenshotApp(root1, 1)
    root2 = tk.Tk()
    app2 = ScreenshotApp(root2, 2)

    # Передаем ссылки на экземпляры приложений
    app1.other_app = app2
    app2.other_app = app1

    root1.mainloop()
    root2.mainloop()
