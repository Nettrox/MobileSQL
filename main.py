
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
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

    # ScrollView ekliyoruz
    scroll_view = ScrollView(size_hint=(1, 1))
    
    # Mesajı içine alacak bir Label ekliyoruz
    message_label = Label(text=message, font_size='18sp', size_hint_y=None)
    message_label.bind(texture_size=message_label.setter('size'))  # Mesaj metninin boyutuna göre ayarlama yapıyoruz
    scroll_view.add_widget(message_label)

    close_button = Button(text="Close", size_hint=(1, 0.1))
    layout.add_widget(scroll_view)
    layout.add_widget(close_button)

    # Popup boyutunu daha da büyük yapıyoruz
    popup = Popup(title="Message", content=layout, size_hint=(0.9, 0.95))  # %90 genişlik, %95 yükseklik
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
            connection.close()

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

        # Geçmiş Butonu
        history_button = Button(text="History", size_hint=(1, 0.2))
        history_button.bind(on_press=self.show_history)
        layout.add_widget(history_button)

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
            connection.close()

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

            query_users_list = "SELECT username, admin_check FROM person_data WHERE username = %s"
            cursor.execute(query_users_list, (recipient_username,))
            recipient_exists = cursor.fetchone()

            if recipient_exists:
                query_meeple_point = "SELECT meeple_point, admin_check FROM person_data WHERE username = %s"
                cursor.execute(query_meeple_point, (username,))
                sender_points = cursor.fetchone()

                transactionID_max_value = "SELECT transactionID FROM logs WHERE transactionID = (SELECT MAX(transactionID) FROM logs)"
                cursor.execute(transactionID_max_value)
                result = cursor.fetchone()
                transaction_id = result['transactionID']
                #print(transaction_id)  # Sadece sayıyı yazdırır

                if recipient_exists['admin_check'] != 2:
                    if sender_points and sender_points['meeple_point'] >= points_to_send + 1 and sender_points['admin_check'] != 2:
                        # Gönderenin puanını güncelle
                        query_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point - %s WHERE username = %s"
                        cursor.execute(query_send_meeple_point, (points_to_send+1, username))

                        # Alıcının puanını güncelle
                        query_pending_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point + %s WHERE username = %s"
                        cursor.execute(query_pending_send_meeple_point, (points_to_send, recipient_username))

                        transaction_logs = "INSERT INTO logs (transactionID, from_whom, to_who, how_much) VALUES (%s, %s, %s, %s)"
                        cursor.execute(transaction_logs, (transaction_id+1, username, recipient_username, points_to_send))

                        connection.commit()

                        self.send_to_input.text = ""
                        self.points_to_send_input.text = ""
                        show_popup(f"Sent {points_to_send} meeple point to {recipient_username}\n1 Meeple Point commission")


                    elif sender_points['admin_check'] == 2:
                        # Admin alıcının puanını güncelle
                        query_pending_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point + %s WHERE username = %s"
                        cursor.execute(query_pending_send_meeple_point, (points_to_send, recipient_username))

                        transaction_logs = "INSERT INTO logs (transactionID, from_whom, to_who, how_much) VALUES (%s, %s, %s, %s)"
                        cursor.execute(transaction_logs, (transaction_id+1, username, recipient_username, points_to_send))

                        connection.commit()

                        self.send_to_input.text = ""
                        self.points_to_send_input.text = ""
                        show_popup(f"Sent {points_to_send} meeple point to {recipient_username}")
                    else:
                        show_popup("Not enough Meeple points!\nDon't forget 1 Meeple Point commission")
                    cursor.close()
                    connection.close()
                elif recipient_exists['admin_check'] == 2:
                    if sender_points and sender_points['meeple_point'] >= points_to_send:
                        # Gönderenin puanını güncelle
                        query_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point - %s WHERE username = %s"
                        cursor.execute(query_send_meeple_point, (points_to_send, username))

                        # Alıcının puanını güncelle
                        query_pending_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point + %s WHERE username = %s"
                        cursor.execute(query_pending_send_meeple_point, (points_to_send, recipient_username))

                        transaction_logs = "INSERT INTO logs (transactionID, from_whom, to_who, how_much) VALUES (%s, %s, %s, %s)"
                        cursor.execute(transaction_logs, (transaction_id+1, username, recipient_username, points_to_send))

                        connection.commit()

                        self.send_to_input.text = ""
                        self.points_to_send_input.text = ""
                        show_popup(f"Sent {points_to_send} meeple point to {recipient_username}")
                    elif sender_points['admin_check'] == 2:
                        # Admin alıcının puanını güncelle
                        query_pending_send_meeple_point = "UPDATE person_data SET meeple_point = meeple_point + %s WHERE username = %s"
                        cursor.execute(query_pending_send_meeple_point, (points_to_send, recipient_username))

                        transaction_logs = "INSERT INTO logs (transactionID, from_whom, to_who, how_much) VALUES (%s, %s, %s, %s)"
                        cursor.execute(transaction_logs, (transaction_id+1, username, recipient_username, points_to_send))

                        connection.commit()

                        self.send_to_input.text = ""
                        self.points_to_send_input.text = ""
                        show_popup(f"Sent {points_to_send} meeple point to {recipient_username}")
                    else:
                        show_popup("Not enough Meeple points!")
                cursor.close()
                connection.close()
            else:
                show_popup("Invalid username!")
        except:
            return


            
    



    def show_history(self, instance):
        username = self.username

        try:
            connection.ping(reconnect=True)
            cursor = connection.cursor()

            # Kullanıcıya gelen puanlar
            query_received = "SELECT transactionID, from_whom, how_much FROM logs WHERE to_who = %s ORDER BY transactionID DESC"
            cursor.execute(query_received, (username,))
            received_logs = cursor.fetchall()

            # Kullanıcının gönderdiği puanlar
            query_sent = "SELECT transactionID, to_who, how_much FROM logs WHERE from_whom = %s ORDER BY transactionID DESC"
            cursor.execute(query_sent, (username,))
            sent_logs = cursor.fetchall()

            # Popup içeriğini oluştur
            history_content = "meeple points coming\nto you:\n"
            if received_logs:
                for log in received_logs:
                    history_content += f"From: {log['from_whom']}, Amount: {log['how_much']}, Transaction ID: {log['transactionID']}\n"
            else:
                history_content += "No transactions.\n"

            history_content += "\nMeeple points sent\nby you:\n"
            if sent_logs:
                for log in sent_logs:
                    history_content += f"To: {log['to_who']}, Amount: {log['how_much']}, Transaction ID: {log['transactionID']}\n"
            else:
                history_content += "No transactions.\n"

            show_popup(history_content)

        finally:
            cursor.close()
            connection.close()


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
