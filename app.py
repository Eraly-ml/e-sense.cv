import sys
import sqlite3
import threading
import cv2
import speech_recognition as sr
from deepface import DeepFace
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
                             QTabWidget, QProgressBar, QComboBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPalette, QBrush
from aiogram import Bot
import asyncio
"""
Hello our dear coder!
This code was written by the e-sense dev team:
  Arkat our computer vision engineer,
  Eraly our ML/Backend engineer.
We hope you will only use this app to control kids.
"""



# Список нецензурных слов
bad_words = [
    'дурак', 'идиот', 'тупой', 'мразь', 'глупый', 'сволочь',
    'ублюдок', 'негодяй', 'козел', 'долбоеб', 'пидорас', 'сучонок', 'чорт', 'хуй', 'в пизду', 'твою мать', 'сука', 'в жопу', 'кал лошадиный', 'говно вонючее',
    'ебать тебя в сраку', 'злоебучая пиздопроёбина', 'сиська', 'урод ебучий', 'член импотента', 'все бабы дуры, а мужики импотенты', 'тварь позорная',
    'минеты делать', 'узкоглазая шлюха', 'малолетка недоёбанная', 'малолетка', 'я хуею', 'затычка в жопе'
]

# Создание базы данных SQLite
def create_database():
    conn = sqlite3.connect("parental_control.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            tg_id TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            emotion TEXT,
            bad_word TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

create_database()

# Регистрация пользователя
def register_user(name, phone, tg_id):
    conn = sqlite3.connect("parental_control.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (name, phone, tg_id) VALUES (?, ?, ?)
    ''', (name, phone, tg_id))
    conn.commit()
    conn.close()

# Отправка сообщений в Telegram
async def send_telegram_message(tg_id, message):
    bot = Bot(token="YOUR_BOT_TOKEN")  # Замените на ваш токен
    await bot.send_message(tg_id, message)
    await bot.close()

# Сохранение отчетов
def save_report(user_id, emotion=None, bad_word=None):
    conn = sqlite3.connect("parental_control.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (user_id, emotion, bad_word) VALUES (?, ?, ?)
    ''', (user_id, emotion, bad_word))
    conn.commit()
    conn.close()

# Анализ эмоций
def detect_emotion(user_id, tg_id):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            vn = DeepFace.analyze(rgb_frame, actions=['emotion'])
            if 'emotion' in vn[0]:
                emotion = vn[0]['emotion']
                if emotion['angry'] > 10:
                    save_report(user_id, emotion='angry')
                    asyncio.run(send_telegram_message(tg_id, "Обнаружена злость!"))
        except Exception as e:
            print(f"Error in emotion detection: {e}")
    cap.release()
    cv2.destroyAllWindows()

# Обнаружение нецензурной лексики
def listen_and_detect(user_id, tg_id):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=None)
                text = recognizer.recognize_google(audio, language="ru-RU")
                for word in bad_words:
                    if word in text.lower():
                        save_report(user_id, bad_word=word)
                        asyncio.run(send_telegram_message(tg_id, f"Обнаружено плохое слово: {word}"))
                        break
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Google Speech Recognition error: {e}")

# Переводы
translations = {
    'en': {
        'phone_number': "Enter phone number:",
        'camera_checkbox': "Enable camera",
        'start_button': "Start Monitoring",
        'donate_info': "You can donate for the development of the project.\nKaspi-gold: 87717693741\nCard: 4400022481633",
        'developers_info': "Main Developer: Arkat Khasanov\nPhone: 87717693741\nInstagram: @arkkatt\nCEO: Nurbakyt Karazhakov\nPhone: +7 702 934 7121",
        'about_info': "The project analyzes emotions and detects foul language and aggressive emotions.",
        'version_info': "Your version: E-sense-2.0",
        'theme_label': "Choose Theme:",
        'language_label': "Choose Language:",
        'background_image_button': "Change Background Image"
    },
    'ru': {
        'phone_number': "Введите номер телефона:",
        'camera_checkbox': "Включить камеру",
        'start_button': "Начать мониторинг",
        'donate_info': "Вы можете пожертвовать деньги на развитие проекта.\nKaspi-gold: 87717693741\nНомер карты: 4400022481633",
        'developers_info': "Главный разработчик: Аркат Хасанов\nТелефон: 87717693741\nInstagram: @arkkatt\nCEO: Нурбакыт Каражаков\nТелефон: +7 702 934 7121",
        'about_info': "Проект анализирует эмоции и выявляет нецензурную лексику и агрессивные эмоции.",
        'version_info': "Ваша версия: E-sense-2.0",
        'theme_label': "Выберите тему:",
        'language_label': "Выберите язык:",
        'background_image_button': "Изменить фон"
    },
    'kk': {
        'phone_number': "Телефон нөмірін енгізіңіз:",
        'camera_checkbox': "Камераны қосу",
        'start_button': "Мониторингті бастау",
        'donate_info': "Жобаны дамыту үшін ақша аудара аласыз.\nKaspi-gold: 87717693741\nКарта нөмірі: 4400022481633",
        'developers_info': "Негізгі әзірлеуші: Аркат Хасанов\nТелефон: 87717693741\nInstagram: @arkkatt\nCEO: Нурбакыт Каражаков\nТелефон: +7 702 934 7121",
        'about_info': "Жоба эмоцияларды талдап, бейәдеп сөздер мен агрессивті эмоцияларды анықтайды.",
        'version_info': "Сіздің нұсқаңыз: E-sense-2.0",
        'theme_label': "Тақырыпты таңдаңыз:",
        'language_label': "Тілді таңдаңыз:",
        'background_image_button': "Фонды өзгерту"
    }
}

# Основной класс приложения
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_language = 'en'  # Язык по умолчанию
        self.initUI()

    def initUI(self):
        # Настройки шрифта
        font = QFont("Roboto", 30)

        # Создание вкладок
        self.tabs = QTabWidget()
        self.tabs.setFont(font)

        # Создание всех вкладок
        self.main_tab = QWidget()
        self.create_main_tab(font)

        self.donation_tab = QWidget()
        self.create_donation_tab(font)

        self.developers_tab = QWidget()
        self.create_developers_tab(font)

        self.about_tab = QWidget()
        self.create_about_tab(font)

        self.version_tab = QWidget()
        self.create_version_tab(font)

        self.settings_tab = QWidget()
        self.create_settings_tab(font)

        # Основной макет
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.setWindowTitle("Parental Control")
        self.resize(1090, 1020)  # Установка размера окна

        # Установка темы
        self.setLightMode()  # Светлая тема по умолчанию
        self.update_translations()

    def create_main_tab(self, font):
        layout = QVBoxLayout()
        self.phone_label = QLabel()
        self.phone_label.setFont(font)
        self.phone_input = QLineEdit(self)
        self.phone_input.setFont(font)
        self.camera_checkbox = QCheckBox()
        self.camera_checkbox.setFont(font)
        self.start_button = QPushButton(self)
        self.start_button.setFont(font)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)

        layout.addWidget(self.phone_label)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.camera_checkbox)
        layout.addWidget(self.start_button)
        layout.addWidget(self.progress_bar)
        self.main_tab.setLayout(layout)

        self.start_button.clicked.connect(self.start_monitoring)

    def create_donation_tab(self, font):
        layout = QVBoxLayout()
        self.donation_info = QLabel()
        self.donation_info.setFont(font)
        layout.addWidget(self.donation_info)
        self.donation_tab.setLayout(layout)

    def create_developers_tab(self, font):
        layout = QVBoxLayout()
        self.developers_info = QLabel()
        self.developers_info.setFont(font)
        layout.addWidget(self.developers_info)
        self.developers_tab.setLayout(layout)

    def create_about_tab(self, font):
        layout = QVBoxLayout()
        self.about_info = QLabel()
        self.about_info.setFont(font)
        layout.addWidget(self.about_info)
        self.about_tab.setLayout(layout)

    def create_version_tab(self, font):
        layout = QVBoxLayout()
        self.version_info = QLabel()
        self.version_info.setFont(font)
        layout.addWidget(self.version_info)
        self.version_tab.setLayout(layout)

    def create_settings_tab(self, font):
        layout = QVBoxLayout()

        # Переключение светлой/темной темы
        self.theme_label = QLabel()
        self.theme_label.setFont(font)
        self.theme_combobox = QComboBox()
        self.theme_combobox.setFont(font)
        self.theme_combobox.addItems(["Light Mode", "Dark Mode"])
        self.theme_combobox.currentIndexChanged.connect(self.change_theme)

        # Выбор языка
        self.language_label = QLabel()
        self.language_label.setFont(font)
        self.language_combobox = QComboBox()
        self.language_combobox.setFont(font)
        self.language_combobox.addItems(["English", "Russian", "Kazakh"])
        self.language_combobox.currentIndexChanged.connect(self.change_language)

        # Кнопка для изменения фона
        self.background_image_button = QPushButton()
        self.background_image_button.setFont(font)
        self.background_image_button.setText("Change Background Image")
        self.background_image_button.clicked.connect(self.change_background_image)

        layout.addWidget(self.theme_label)
        layout.addWidget(self.theme_combobox)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combobox)
        layout.addWidget(self.background_image_button)
        self.settings_tab.setLayout(layout)

    def start_monitoring(self):
        name = "User"  # Замените на ввод имени пользователя
        phone = self.phone_input.text()
        tg_id = "USER_TG_ID"  # Замените на ввод Telegram ID

        if phone and tg_id:
            register_user(name, phone, tg_id)
            conn = sqlite3.connect("parental_control.db")
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
            user_id = cursor.fetchone()[0]
            conn.close()

            if self.camera_checkbox.isChecked():
                threading.Thread(target=detect_emotion, args=(user_id, tg_id), daemon=True).start()
            threading.Thread(target=listen_and_detect, args=(user_id, tg_id), daemon=True).start()
            self.update_progress_bar()

    def update_progress_bar(self):
        self.progress_bar.setValue(50)  # Пример прогресса

    def change_theme(self, index):
        if index == 0:  # Светлая тема
            self.setLightMode()
        else:  # Темная тема
            self.setDarkMode()

    def setLightMode(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #FFF0F5;  /* Светлый розовый */
                color: black;
            }
            QTabWidget::pane { /* Рамка вкладки */
                background-color: #FFD1DA; /* Мягкий розовый */
                border: 1px solid #FBA1B7;
            }
            QTabBar::tab {
                background-color: #FFD1DA; /* Цвет вкладки */
                color: black;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background-color: #FBA1B7; /* Цвет выбранной вкладки */
                color: white;
            }
            QPushButton {
                background-color: #FFD1DA;
                border: 2px solid #FBA1B7;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #FBA1B7;
                color: white;
            }
            QLabel {
                color: #FBA1B7;  /* Цвет текста */
            }
        """)
        self.set_background_image("C:/Users/Admin/Downloads/den-semi.jpg")  # Фоновое изображение

    def setDarkMode(self):
        self.setStyleSheet("background-color: black; color: white;")
        self.theme_label.setText("Тақырыпты таңдаңыз:")
        self.language_label.setText("Тілді таңдаңыз:")
        self.set_background_image("C:/Users/Admin/Downloads/den-semi.jpg")  # Фоновое изображение

    def change_language(self, index):
        languages = ['en', 'ru', 'kk']
        self.current_language = languages[index]
        self.update_translations()

    def update_translations(self):
        lang = translations[self.current_language]
        self.phone_label.setText(lang['phone_number'])
        self.camera_checkbox.setText(lang['camera_checkbox'])
        self.start_button.setText(lang['start_button'])
        self.donation_info.setText(lang['donate_info'])
        self.developers_info.setText(lang['developers_info'])
        self.about_info.setText(lang['about_info'])
        self.version_info.setText(lang['version_info'])
        self.theme_label.setText(lang['theme_label'])
        self.language_label.setText(lang['language_label'])
        self.background_image_button.setText(lang['background_image_button'])

    def set_background_image(self, image_path):
        if image_path:
            pixmap = QPixmap(image_path)
            palette = self.palette()
            palette.setBrush(QPalette.Background, QBrush(pixmap))
            self.setPalette(palette)
        else:
            self.setStyleSheet("background-color: white;")

    def change_background_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Images (*.png *.jpg *.bmp)",
                                                   options=options)
        if file_path:
            self.set_background_image(file_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())
