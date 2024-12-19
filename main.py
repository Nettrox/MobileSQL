from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
import pymysql

from kivy.uix.popup import Popup

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="meepleandpeople",
    host="mysql-3be53b35-nettroxaksu-6ad7.l.aivencloud.com",
    password="AVNS_OSg2FqUphr6pTer9cW4",
    read_timeout=timeout,
    port=22697,
    user="avnadmin",
    write_timeout=timeout,
)

def show_popup(message):
    layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
    label = Label(text=message, font_size='18sp')
    close_button = Button(text="Close", size_hint=(1, 0.2))
    layout.add_widget(label)
    layout.add_widget(close_button)

    popup = Popup(title="Message", content=layout, size_hint=(0.6, 0.4))
    close_button.bind(on_press=popup.dismiss)
    popup.open()

# Giriş Ekranı
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Kullanıcı adı ve şifre girişleri
        self.username_input = TextInput(hint_text="Username", multiline=False)
        self.password_input = TextInput(hint_text="Password", multiline=False, password=True)

        # Giriş Butonu
        login_button = Button(text="Login", size_hint=(1, 0.2))
        login_button.bind(on_press=self.verify_credentials)

        # Layout düzenlemesi
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_button)

        self.add_widget(layout)

    def verify_credentials(self, instance):
        username = self.username_input.text
        password = self.password_input.text

        try:
            connection.ping(reconnect=True)
            cursor = connection.cursor()

            query = "SELECT password, username FROM person_data WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            results_entry = cursor.fetchall()

            self.username_input.text = ""
            self.password_input.text = ""

            if results_entry:
                self.manager.current = "main_screen"  # Ana ekrana geçiş
                self.manager.get_screen("main_screen").username = username  # Kullanıcı adını Ana Ekrana geç
            else:
                show_popup("Wrong username or password!")
        finally:
            cursor.close()

# Ana Ekran
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Üst çubuk düzeni
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))

        # Logout Butonu
        logout_button = Button(text="Logout", size_hint=(0.2, 1))
        logout_button.bind(on_press=self.logout)
        top_bar.add_widget(logout_button)

        layout.add_widget(top_bar)

        # Puan Gösterimi
        self.point_label = Label(text="Your Meeple Point: [Fetching...]", font_size='20sp')
        layout.add_widget(self.point_label)

        # Güncelleme Butonu
        refresh_button = Button(text="Refresh Meeple Point", size_hint=(1, 0.2))
        refresh_button.bind(on_press=self.refresh_points)
        layout.add_widget(refresh_button)

        # Puan Yollama Bölümü
        self.send_to_input = TextInput(hint_text="Send to (Username)", multiline=False)
        self.points_to_send_input = TextInput(hint_text="Amount of Points", multiline=False)

        # Puan Gönder Butonu
        send_button = Button(text="Send Points", size_hint=(1, 0.2))
        send_button.bind(on_press=self.send_points)

        layout.add_widget(self.send_to_input)
        layout.add_widget(self.points_to_send_input)
        layout.add_widget(send_button)

        self.add_widget(layout)

    def logout(self, instance):
        # Logout işlevi
        self.manager.current = "login_screen"

    def refresh_points(self, instance):
        username = self.username  # Kullanıcı adı artık burada mevcut

        try:
            connection.ping(reconnect=True)
            cursor = connection.cursor()

            query_meeple_point = "SELECT meeple_point FROM person_data WHERE username = %s"
            cursor.execute(query_meeple_point, (username,))
            result = cursor.fetchone()

            if result:
                self.point_label.text = f"Your Meeple Point: {result['meeple_point']}"
            else:
                show_popup("Failed to fetch meeple points!")
        finally:
            cursor.close()

    def send_points(self, instance):
        recipient_username = self.send_to_input.text
        points_to_send = self.points_to_send_input.text

        if not points_to_send.isdigit():
            show_popup("Invalid meeple point!")
            self.send_to_input.text = ""
            self.points_to_send_input.text = ""
            return

        points_to_send = int(points_to_send)
        username = self.username

        try:
            connection.ping(reconnect=True)
            cursor = connection.cursor()

            query_users_list = "SELECT username FROM person_data WHERE username = %s"
            cursor.execute(query_users_list, (recipient_username,))
            recipient_exists = cursor.fetchone()

            if recipient_exists:
                query_meeple_point = "SELECT meeple_point FROM person_data WHERE username = %s"
                cursor.execute(query_meeple_point, (username,))
                sender_points = cursor.fetchone()

                if sender_points and sender_points['meeple_point'] >= points_to_send:
                    # Gönderenin puanını güncelle
                    query_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point - %s WHERE username = %s"
                    cursor.execute(query_send_meeple_point, (points_to_send, username))

                    # Alıcının puanını güncelle
                    query_pending_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point + %s WHERE username = %s"
                    cursor.execute(query_pending_send_meeple_point, (points_to_send, recipient_username))

                    connection.commit()

                    self.send_to_input.text = ""
                    self.points_to_send_input.text = ""
                    show_popup(f"Sent {points_to_send} meeple point to {recipient_username}")
                else:
                    show_popup("Not enough Meeple points!")
            else:
                show_popup("Invalid username!")
        finally:
            cursor.close()

# Uygulama Yapısı
class MeeplePointApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(MainScreen(name="main_screen"))
        return sm

# Uygulamayı başlat
if __name__ == "__main__":
    MeeplePointApp().run()
