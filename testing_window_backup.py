import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import random
import io
import pygame
import os
import speech_recognition as sr
from main import BaseWindow
from styles import StyledCanvas, StyledButton, PlacedStyledButton


pygame.mixer.init()  # Инициализация pygame.mixer

# Глобальная переменная для активного пользователя
ACTIVE_USER = {}

# Функция для загрузки активного пользователя
def load_active_user():
    global ACTIVE_USER
    try:
        with sqlite3.connect("team_app.db") as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT user_id, nickname, image FROM users LIMIT 1")
            user = cursor.fetchone()
            if user:
                ACTIVE_USER['user_id'] = user[0]
                ACTIVE_USER['nickname'] = user[1]
                ACTIVE_USER['image'] = user[2] if user[2] else None
            else:
                ACTIVE_USER = {'user_id': None, 'nickname': 'Unknown', 'image': None}
    except sqlite3.Error as e:
        messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить пользователя: {e}")

# Загрузка активного пользователя при старте программы
load_active_user()

class TopicSelectionScreen:
    def __init__(self, master, on_start_test):
        self.master = master
        self.on_start_test = on_start_test
        self.selected_topic = None
        self.selected_test = None
        self.topic_buttons = {}
        self.test_buttons = {}
        self.setup_ui()

    def setup_ui(self):
        self.clear_window()
        self.master.geometry('800x600')
        self.master.title("Выбор темы урока")

        self.canvas = StyledCanvas(self.master)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.top_frame = tk.Frame(self.master, height=50, bg='white')
        self.top_frame.pack(fill=tk.X)

        self.user_image_label = tk.Label(self.top_frame, bg='white')
        self.user_image_label.place(x=10, y=5)
        self.show_user_info()

        self.title_label = tk.Label(self.top_frame, text="Выберите тему урока", font=('Helvetica', 24, 'bold'), bg='white')
        self.title_label.pack(pady=10)

        topics = self.load_topics()
        for idx, topic in enumerate(topics):
            topic_button = StyledButton(self.canvas, text=topic[1], command=lambda t=topic: self.select_topic(t), x=150, y=150 + idx*80, width=250, height=60)
            self.topic_buttons[topic[0]] = topic_button

        tests = self.load_tests()
        for idx, test in enumerate(tests):
            test_button = StyledButton(self.canvas, text=test[1], command=lambda t=test: self.select_test(t), x=650, y=150 + idx*80, width=250, height=60)
            self.test_buttons[test[0]] = test_button

        self.start_button = StyledButton(self.canvas, text="Начать тестирование", command=self.start_test, x=400, y=500, width=250, height=60)

        self.exit_button = StyledButton(self.canvas, text="Выход", command=self.master.quit, x=750, y=550, width=100, height=50)

        self.back_button = StyledButton(self.canvas, text="Назад", command=self.master.quit, x=50, y=550, width=100, height=50)

    def show_user_info(self):
        global ACTIVE_USER
        nickname = ACTIVE_USER.get('nickname', 'Unknown')
        image_data = ACTIVE_USER.get('image')

        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((40, 40))
            photo = ImageTk.PhotoImage(image)
        else:
            image = Image.new('RGB', (40, 40), color='black')
            photo = ImageTk.PhotoImage(image)

        self.user_image_label.configure(image=photo)
        self.user_image_label.image = photo

        self.user_name_label = tk.Label(self.top_frame, text=nickname, font=('Helvetica', 16), bg='white')
        self.user_name_label.place(x=60, y=10)

    def load_topics(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT topic_id, topic_name FROM topics")
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить темы: {e}")
            return []

    def load_tests(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT test_id, test_name, test_type FROM tests")
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить тесты: {e}")
            return []

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def select_topic(self, topic):
        self.selected_topic = topic
        for btn in self.topic_buttons.values():
            btn.set_image(btn.normal_photo)
        self.topic_buttons[topic[0]].set_image(self.topic_buttons[topic[0]].pressed_photo)

    def select_test(self, test):
        self.selected_test = test
        for btn in self.test_buttons.values():
            btn.set_image(btn.normal_photo)
        self.test_buttons[test[0]].set_image(self.test_buttons[test[0]].pressed_photo)

    def start_test(self):
        if self.selected_topic and self.selected_test:
            self.on_start_test(self.selected_topic, self.selected_test)
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите тему и тест.")

class MainTestApp:
    def __init__(self, root):
        self.root = root
        self.show_topic_selection_screen()

    def show_topic_selection_screen(self):
        self.topic_selection_screen = TopicSelectionScreen(self.root, self.start_lesson)

    def start_lesson(self, topic, test):
        lesson_window = tk.Toplevel(self.root)
        test_type = test[2]
        if test_type == 1:
            WordLessonScreen(lesson_window, topic, test)
        elif test_type == 2:
            WordWriteScreen(lesson_window, topic, test)
        elif test_type == 3:
            WordAudioScreen(lesson_window, topic, test)
        elif test_type == 4:
            WordSpeakScreen(lesson_window, topic, test)

class TestingWindow(BaseWindow):
    def __init__(self, root, main_root, current_user):
        super().__init__(root, main_root, current_user)
        self.root.title("Программа обучения английскому языку - Тестирование")
        self.app = MainTestApp(self.root)

class BaseLessonScreen:
    def __init__(self, master, topic, test):
        self.master = master
        self.topic = topic
        self.test = test
        self.score = 0
        self.current_word_index = 0
        self.words = []

        self.setup_ui()

    def setup_ui(self):
        self.clear_window()
        self.master.geometry('800x600')
        self.master.minsize(800, 600)
        self.master.maxsize(800, 600)
        self.master.title(f"Тема: {self.topic[1]}")

        self.canvas = StyledCanvas(self.master)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.top_frame = tk.Frame(self.master, height=50, bg='white')
        self.top_frame.pack(fill=tk.X)

        self.user_image_label = tk.Label(self.top_frame, bg='white')
        self.user_image_label.place(x=10, y=5)
        self.show_user_info()

        self.topic_label = tk.Label(self.top_frame, text=f"Тема: {self.topic[1]}", font=('Helvetica', 20, 'bold'), bg='white')
        self.topic_label.pack(pady=10)

        self.score_label = tk.Label(self.top_frame, text=f"Баллы: {self.score}/8", font=('Helvetica', 14), bg='white')
        self.score_label.place(x=790, y=10, anchor=tk.NE)

        self.image_label = tk.Label(self.master)
        self.image_label.pack(pady=10)

        self.progress_frame = tk.Frame(self.master)
        self.progress_frame.pack(pady=10)
        self.create_progress_bar()

        self.word_label = tk.Label(self.master, font=('Helvetica', 24, 'bold'))
        self.word_label.pack(pady=10)

        self.prev_button = StyledButton(self.canvas, text="Предыдущее слово", command=self.prev_word, x=100, y=500, width=200, height=50)
        self.next_button = StyledButton(self.canvas, text="Следующее слово", command=self.next_word, x=700, y=500, width=200, height=50)

        self.buttons_frame = tk.Frame(self.master)
        self.buttons_frame.pack(pady=10)

        self.message_label = tk.Label(self.master, font=('Helvetica', 16, 'bold'))
        self.message_label.pack(pady=10)

        self.exit_button = StyledButton(self.canvas, text="Выход", command=self.master.quit, x=750, y=550, width=100, height=50)
        self.back_button = StyledButton(self.canvas, text="Выбрать тест", command=self.return_to_selection, x=50, y=550, width=100, height=50)

    def show_user_info(self):
        global ACTIVE_USER
        nickname = ACTIVE_USER.get('nickname', 'Unknown')
        image_data = ACTIVE_USER.get('image')

        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((40, 40))
            photo = ImageTk.PhotoImage(image)
        else:
            image = Image.new('RGB', (40, 40), color='black')
            photo = ImageTk.PhotoImage(image)

        self.user_image_label.configure(image=photo)
        self.user_image_label.image = photo

        self.user_name_label = tk.Label(self.top_frame, text=nickname, font=('Helvetica', 16), bg='white')
        self.user_name_label.place(x=60, y=10)

    def create_progress_bar(self):
        self.progress_canvas = tk.Canvas(self.progress_frame, width=240, height=20)
        self.progress_canvas.pack()
        self.progress_segments = []
        for i in range(8):
            segment = self.progress_canvas.create_oval(i * 30 + 5, 5, (i + 1) * 30 - 10, 20, fill="gray")
            self.progress_segments.append(segment)

    def update_progress(self, correct):
        color = "green" if correct else "red"
        self.progress_canvas.itemconfig(self.progress_segments[self.current_word_index], fill=color)

    def clear_window(self):
        for widget in self.master.winfo_children():
            widget.destroy()

    def return_to_selection(self):
        self.master.destroy()

    def prev_word(self):
        pass

    def next_word(self):
        pass

    def check_answer(self, chosen, correct, sound_data):
        pass

    def show_word(self):
        pass

    def play_sound(self, sound_data):
        try:
            with open("temp_sound.mp3", "wb") as f:
                f.write(sound_data)
            pygame.mixer.init()
            pygame.mixer.music.load("temp_sound.mp3")
            pygame.mixer.music.play()
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            self.master.bind("<Destroy>", self.cleanup_temp_file)
            self.master.after(100, self.check_music_end)
        except Exception as e:
            messagebox.showerror("Ошибка воспроизведения звука", f"Не удалось воспроизвести звук: {e}")

    def check_music_end(self):
        if not pygame.mixer.music.get_busy():
            self.cleanup_temp_file()
        else:
            self.master.after(100, self.check_music_end)

    def cleanup_temp_file(self, event=None):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            if os.path.exists("temp_sound.mp3"):
                os.remove("temp_sound.mp3")
        except Exception as e:
            print(f"Ошибка при удалении временного файла: {e}")

    def save_test_result(self):
        global ACTIVE_USER
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    INSERT INTO testing_stats (user_id, test_id, testing_counter)
                    VALUES (?, ?, ?)
                """, (ACTIVE_USER['user_id'], self.test[0], self.score))
                connection.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось сохранить результаты теста: {e}")

class WordLessonScreen(BaseLessonScreen):
    def __init__(self, master, topic, test):
        super().__init__(master, topic, test)
        self.all_words = []
        self.load_words()
        self.show_word()

    def load_words(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT w.english, w.russian, w.picture, w.sound
                    FROM words w
                    JOIN words_groupings wg ON w.word_id = wg.word_id
                    JOIN topics t ON wg.topic_id = t.topic_id
                    WHERE t.topic_id = ?
                """, (self.topic[0],))
                self.all_words = cursor.fetchall()
                self.words = random.sample(self.all_words, 8)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить слова: {e}")

    def show_word(self):
        self.message_label.config(text="")
        if self.words:
            english, russian, picture_data, sound_data = self.words[self.current_word_index]
            image = Image.open(io.BytesIO(picture_data))
            image = image.resize((256, 256))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            self.word_label.config(text=russian)

            for widget in self.canvas.winfo_children():
                if isinstance(widget, PlacedStyledButton):
                    widget.destroy()

            all_words = [word[0] for word in self.all_words if word[0] != english]
            random_words = random.sample(all_words, 5)
            random_words.append(english)
            random.shuffle(random_words)

            # Добавляем изображение на холст
            self.canvas.create_image(400, 200, image=photo, anchor=tk.CENTER)

            for idx, btn_text in enumerate(random_words):
                btn = PlacedStyledButton(self.canvas, text=btn_text,
                                         command=lambda b=btn_text, s=sound_data: self.check_answer(b, english, s),
                                         x=150 + idx * 150, y=450, width=120, height=50)
                self.canvas.create_window(150 + idx * 150, 450, window=btn)

            # Добавляем другие элементы на холст
            self.prev_button = PlacedStyledButton(self.canvas, text="Предыдущее слово", command=self.prev_word, x=100, y=550, width=200, height=50)
            self.next_button = PlacedStyledButton(self.canvas, text="Следующее слово", command=self.next_word, x=400, y=550, width=200, height=50)
            self.exit_button = PlacedStyledButton(self.canvas, text="Выход", command=self.master.quit, x=700, y=550, width=100, height=50)
            self.back_button = PlacedStyledButton(self.canvas, text="Выбрать тест", command=self.return_to_selection, x=100, y=500, width=200, height=50)

            self.canvas.create_window(100, 550, window=self.prev_button)
            self.canvas.create_window(400, 550, window=self.next_button)
            self.canvas.create_window(700, 550, window=self.exit_button)
            self.canvas.create_window(100, 500, window=self.back_button)

    def check_answer(self, chosen, correct, sound_data):
        for widget in self.canvas.winfo_children():
            if isinstance(widget, PlacedStyledButton):
                widget.config(state=tk.DISABLED)

        if chosen == correct:
            self.score += 1
            self.message_label.config(text="Правильно!", fg='green')
            self.play_sound(sound_data)
            self.update_progress(True)
        else:
            self.message_label.config(text="Неправильно!", fg='red')
            self.update_progress(False)
        self.score_label.config(text=f"Баллы: {self.score}/8")

        if self.current_word_index == len(self.words) - 1:
            self.end_test()
        else:
            self.next_button.config(state=tk.NORMAL)

    def next_word(self):
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.show_word()

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.show_word()

    def end_test(self):
        self.message_label.config(text=f"Тест окончен! Ваши баллы: {self.score}/8", fg='black')
        for widget in self.canvas.winfo_children():
            if isinstance(widget, PlacedStyledButton):
                widget.config(state=tk.DISABLED)
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.save_test_result()






# Повторите ту же процедуру для WordWriteScreen, WordAudioScreen и WordSpeakScreen
# ...
class WordWriteScreen(BaseLessonScreen):
    def __init__(self, master, topic, test):
        super().__init__(master, topic, test)
        self.load_words()
        self.show_word()

    def load_words(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT w.english, w.russian, w.picture, w.sound
                    FROM words w
                    JOIN words_groupings wg ON w.word_id = wg.word_id
                    JOIN topics t ON wg.topic_id = t.topic_id
                    WHERE t.topic_id = ?
                """, (self.topic[0],))
                self.words = cursor.fetchall()
                random.shuffle(self.words)
                self.words = self.words[:8]
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить слова: {e}")

    def show_word(self):
        self.message_label.config(text="")
        if self.words:
            english, russian, picture_data, sound_data = self.words[self.current_word_index]
            image = Image.open(io.BytesIO(picture_data))
            image = image.resize((256, 256))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            self.word_label.config(text=russian)

            for widget in self.buttons_frame.winfo_children():
                widget.destroy()

            input_label = tk.Label(self.buttons_frame, text="Введите это слово на английском языке:",
                                   font=('Helvetica', 12))
            input_label.pack(pady=5)

            self.input_entry = tk.Entry(self.buttons_frame, font=('Helvetica', 12))
            self.input_entry.pack(pady=5)

            check_button = PlacedStyledButton(self.buttons_frame, text="Проверить",
                                              command=lambda s=sound_data: self.check_answer(self.input_entry.get(),
                                                                                             english, s),
                                              width=200, height=50)
            check_button.pack(pady=5)

    def check_answer(self, chosen, correct, sound_data):
        if chosen.strip().lower() == correct.lower():
            self.score += 1
            self.message_label.config(text="Правильно!", fg='green')
            self.play_sound(sound_data)
            self.update_progress(True)
        else:
            self.message_label.config(text="Неправильно!", fg='red')
            self.update_progress(False)
        self.score_label.config(text=f"Баллы: {self.score}/8")

        self.input_entry.config(state=tk.DISABLED)

        if self.current_word_index == len(self.words) - 1:
            self.end_test()
        else:
            self.next_button.config(state=tk.NORMAL)

    def next_word(self):
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.show_word()

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.show_word()

    def end_test(self):
        self.message_label.config(text=f"Тест окончен! Ваши баллы: {self.score}/8", fg='black')
        self.input_entry.config(state=tk.DISABLED)
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.save_test_result()

class WordAudioScreen(BaseLessonScreen):
    def __init__(self, master, topic, test):
        super().__init__(master, topic, test)
        self.all_words = []
        self.load_words()
        self.show_word()

    def load_words(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT w.english, w.russian, w.picture, w.sound
                    FROM words w
                    JOIN words_groupings wg ON w.word_id = wg.word_id
                    JOIN topics t ON wg.topic_id = t.topic_id
                    WHERE t.topic_id = ?
                """, (self.topic[0],))
                self.all_words = cursor.fetchall()
                self.words = random.sample(self.all_words, 8)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить слова: {e}")

    def show_word(self):
        self.message_label.config(text="")
        if self.words:
            english, russian, picture_data, sound_data = self.words[self.current_word_index]

            image = Image.new('RGB', (256, 256), color='gray')
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo

            for widget in self.buttons_frame.winfo_children():
                widget.destroy()

            play_audio_button = PlacedStyledButton(self.buttons_frame, text="Воспроизвести аудио",
                                                   command=lambda s=sound_data: self.play_sound(s),
                                                   width=200, height=50)
            play_audio_button.pack(pady=5)

            all_words = [word[1] for word in self.all_words if word[1] != russian]
            random_words = random.sample(all_words, 5)
            random_words.append(russian)
            random.shuffle(random_words)

            for idx, btn_text in enumerate(random_words):
                btn = PlacedStyledButton(self.buttons_frame, text=btn_text,
                                         command=lambda b=btn_text: self.check_answer(b, russian, sound_data),
                                         width=200, height=50)
                btn.pack(side=tk.LEFT, padx=5, pady=5)

    def check_answer(self, chosen, correct, sound_data):
        for btn in self.buttons_frame.winfo_children():
            btn.config(state=tk.DISABLED)

        if chosen == correct:
            self.score += 1
            self.message_label.config(text="Правильно!", fg='green')
            self.play_sound(sound_data)
            self.update_progress(True)
        else:
            self.message_label.config(text="Неправильно!", fg='red')
            self.update_progress(False)
        self.score_label.config(text=f"Баллы: {self.score}/8")

        if self.current_word_index == len(self.words) - 1:
            self.end_test()
        else:
            self.next_button.config(state=tk.NORMAL)

    def next_word(self):
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.show_word()

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.show_word()

    def end_test(self):
        self.message_label.config(text=f"Тест окончен! Ваши баллы: {self.score}/8", fg='black')
        for btn in self.buttons_frame.winfo_children():
            btn.config(state=tk.DISABLED)
        self.prev_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.DISABLED)
        self.save_test_result()

class WordSpeakScreen(BaseLessonScreen):
    def __init__(self, master, topic, test):
        super().__init__(master, topic, test)
        self.all_words = []
        self.load_words()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.show_word()

    def load_words(self):
        try:
            with sqlite3.connect("team_app.db") as connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT w.english, w.russian, w.picture, w.sound
                    FROM words w
                    JOIN words_groupings wg ON w.word_id = wg.word_id
                    JOIN topics t ON wg.topic_id = t.topic_id
                    WHERE t.topic_id = ?
                """, (self.topic[0],))
                self.all_words = cursor.fetchall()
                self.words = random.sample(self.all_words, 8)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить слова: {e}")

    def show_word(self):
        self.message_label.config(text="")
        if self.words:
            english, russian, picture_data, sound_data = self.words[self.current_word_index]
            image = Image.open(io.BytesIO(picture_data))
            image = image.resize((256, 256))
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
            self.word_label.config(text=russian)

            for widget in self.buttons_frame.winfo_children():
                widget.destroy()

            speak_button = PlacedStyledButton(self.buttons_frame, text="Произнесите слово на английском",
                                              command=lambda: self.recognize_speech(english, sound_data),
                                              width=250, height=60)
            speak_button.pack(pady=5)

    def recognize_speech(self, correct_word, sound_data):
        with self.microphone as source:
            audio = self.recognizer.listen(source)

        try:
            recognized_text = self.recognizer.recognize_google(audio, language="en-US").lower()
            self.check_answer(recognized_text, correct_word, sound_data)
        except sr.UnknownValueError:
            self.message_label.config(text="Не удалось распознать речь. Попробуйте еще раз.", fg='red')
        except sr.RequestError as e:
            messagebox.showerror("Ошибка распознавания", f"Ошибка сервиса распознавания речи: {e}")

    def check_answer(self, chosen, correct, sound_data):
        if chosen.strip().lower() == correct.lower():
            self.score += 1
            self.message_label.config(text="Правильно!", fg='green')
            self.play_sound(sound_data)
            self.update_progress(True)
        else:
            self.message_label.config(text="Неправильно!", fg='red')
            self.update_progress(False)
        self.score_label.config(text=f"Баллы: {self.score}/8")

        if self.current_word_index == len(self.words) - 1:
            self.end_test()
        else:
            self.next_button.config(state=tk.NORMAL)

    def next_word(self):
        if self.current_word_index < len(self.words) - 1:
            self.current_word_index += 1
            self.show_word()

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.show_word()

    def end_test(self):
        self.message_label.config(text=f"Тест окончен! Ваши баллы: {self.score}/8", fg='black')
        self.next_button.config(state=tk.DISABLED)
        self.save_test_result()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainTestApp(root)
    root.mainloop()

