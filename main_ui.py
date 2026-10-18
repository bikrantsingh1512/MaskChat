from kivymd.app import MDApp
from kivy.core.window import Window  
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
import requests

Window.size = (360, 640)

KV = '''
ScreenManager:
    LoginScreen:
    RegisterScreen:
    HomeScreen:
    ChatScreen:

<LoginScreen>:
    name: 'login'
    MDBoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "15dp"
        md_bg_color: 0.05, 0.05, 0.05, 1 

        MDLabel:
            text: "MaskChat"
            font_style: "H3"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0, 0.8, 0.4, 1 
            size_hint_y: None
            height: "100dp"

        MDTextField:
            id: login_id
            hint_text: "Username or Gmail"
            mode: "rectangle"

        MDTextField:
            id: password
            hint_text: "Password"
            password: True
            mode: "rectangle"

        MDRaisedButton:
            text: "LOGIN"
            md_bg_color: 0, 0.8, 0.4, 1
            text_color: 0, 0, 0, 1
            size_hint_x: 1
            on_release: root.do_login()

        MDFlatButton:
            text: "New User? Register Already"
            theme_text_color: "Custom"
            text_color: 0, 0.8, 0.4, 1
            pos_hint: {"center_x": .5}
            on_release: root.manager.current = 'register'

        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: "70dp"
            spacing: "4dp"

            MDLabel:
                text: "Developed by Next Gen Developers"
                font_style: "Caption"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 0.4

            MDLabel:
                text: "Bikrant Singh"
                font_style: "Subtitle2"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0, 0.8, 0.4, 0.8

<RegisterScreen>:
    name: 'register'
    MDBoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "15dp"
        md_bg_color: 0.05, 0.05, 0.05, 1

        MDLabel:
            text: "Create Account"
            font_style: "H4"
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0, 0.8, 0.4, 1
            size_hint_y: None
            height: "80dp"

        MDTextField:
            id: reg_username
            hint_text: "Create Unique Username"
            mode: "rectangle"

        MDTextField:
            id: reg_email
            hint_text: "Gmail Address"
            mode: "rectangle"

        MDTextField:
            id: reg_password
            hint_text: "Create App Password"
            password: True
            mode: "rectangle"

        MDRaisedButton:
            text: "REGISTER"
            md_bg_color: 0, 0.8, 0.4, 1
            text_color: 0, 0, 0, 1
            size_hint_x: 1
            on_release: root.do_register()

        MDFlatButton:
            text: "Already Registered? Login"
            theme_text_color: "Custom"
            text_color: 0, 0.8, 0.4, 1
            pos_hint: {"center_x": .5}
            on_release: root.manager.current = 'login'

<HomeScreen>:
    name: 'home'
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.08, 0.08, 0.08, 1

        MDTopAppBar:
            title: "MaskChat"
            right_action_items: [["magnify", lambda x: root.search_username()]]
            md_bg_color: 0, 0.6, 0.3, 1

        MDLabel:
            text: "No Active Chats. Click Search icon to find friends."
            halign: "center"
            theme_text_color: "Custom"
            text_color: 1, 1, 1, 0.4

        MDRaisedButton:
            text: "Open Demo Chat Window"
            pos_hint: {"center_x": .5}
            md_bg_color: 0, 0.6, 0.3, 1
            on_release: root.manager.current = 'chat'

<ChatScreen>:
    name: 'chat'
    on_leave: root.lock_chat_on_exit() 
    MDBoxLayout:
        orientation: 'vertical'
        md_bg_color: 0.05, 0.05, 0.05, 1

        MDTopAppBar:
            id: chat_title
            title: "Chat: Gemini (Masked 🔒)"
            right_action_items: [["dots-vertical", lambda x: root.show_unlock_popup()]]
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            md_bg_color: 0, 0.6, 0.3, 1

        ScrollView:
            MDList:
                id: message_list
                padding: "15dp"
                spacing: "12dp"

        MDBoxLayout:
            size_hint_y: None
            height: "60dp"
            padding: "8dp"
            spacing: "10dp"
            md_bg_color: 0.1, 0.1, 0.1, 1

            MDTextField:
                id: type_message
                hint_text: "Type secure message..."
                mode: "line"
                text_color_normal: 1, 1, 1, 1

            MDIconButton:
                icon: "send"
                theme_text_color: "Custom"
                text_color: 0, 0.8, 0.4, 1
                on_release: root.send_secure_message()
'''

API_BASE_URL = "http://127.0.0.1:8000" 
CURRENT_USER_ID = None

class LoginScreen(Screen):
    def do_login(self):
        global CURRENT_USER_ID
        login_id = self.ids.login_id.text
        password = self.ids.password.text
        payload = {"login_id": login_id, "password": password}
        try:
            response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
            if response.status_code == 200:
                CURRENT_USER_ID = response.json().get("user_id")
                self.manager.current = 'home'
        except:
            self.manager.current = 'home'

class RegisterScreen(Screen):
    def do_register(self):
        username = self.ids.reg_username.text
        email = self.ids.reg_email.text
        password = self.ids.reg_password.text
        payload = {"username": username, "email": email, "password": password}
        try:
            response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
            if response.status_code == 200:
                self.manager.current = 'login'
        except:
            self.manager.current = 'login'

class HomeScreen(Screen):
    def search_username(self):
        print("Searching user...")

class ChatScreen(Screen):
    is_unlocked = False

    def on_enter(self):
        self.load_chat_ui(unlock=False)

    def load_chat_ui(self, unlock=False):
        self.ids.message_list.clear_widgets()
        from kivymd.uix.label import MDLabel
        
        if not unlock:
            self.ids.chat_title.title = "Chat: Gemini (Masked 🔒)"
            masked_data = ["*#@&%x9!", "pQ7!$kL2", "98x#@!aZ"]
            for txt in masked_data:
                lbl = MDLabel(text=f"Gemini: {txt}", theme_text_color="Custom", text_color=(1,1,1,0.4))
                self.ids.message_list.add_widget(lbl)
        else:
            self.ids.chat_title.title = "Chat: Gemini (Unlocked 🔓)"
            real_data = ["Hey Bikrant!", "Project is ready.", "Let's launch Next Gen Apps!"]
            for txt in real_data:
                lbl = MDLabel(text=f"Gemini: {txt}", theme_text_color="Custom", text_color=(0, 0.8, 0.4, 1))
                self.ids.message_list.add_widget(lbl)

    def show_unlock_popup(self):
        if not self.is_unlocked:
            self.is_unlocked = True
            self.load_chat_ui(unlock=True)
        else:
            self.is_unlocked = False
            self.load_chat_ui(unlock=False)

    def lock_chat_on_exit(self):
        self.is_unlocked = False
        self.ids.message_list.clear_widgets()

    def send_secure_message(self):
        text = self.ids.type_message.text
        if text:
            self.ids.type_message.text = ""

    def go_back(self):
        self.manager.current = 'home'

class MaskChatApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        return Builder.load_string(KV)

if __name__ == '__main__':
    MaskChatApp().run()
