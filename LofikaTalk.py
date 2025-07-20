def make_rounded_avatar(pil_img, size=(40, 40)):
    pil_img = pil_img.convert("RGBA").resize(size, Image.LANCZOS)
    mask = Image.new('L', size, 0)
    draw = Image.new('L', size, 0)
    from PIL import ImageDraw
    ImageDraw.Draw(mask).ellipse((0, 0, size[0], size[1]), fill=255)
    result = Image.new('RGBA', size)
    result.paste(pil_img, (0, 0), mask=mask)
    return result

import base64
import io
import threading
import datetime
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image


class MainWindow(CTk):
   def change_avatar(self):
       filetypes = [('Зображення', '*.png *.jpg *.jpeg *.gif *.bmp')]
       path = filedialog.askopenfilename(title='Оберіть новий аватар', filetypes=filetypes)
       if path:
           try:
               pil_img = Image.open(path)
               rounded = make_rounded_avatar(pil_img, size=(40, 40))
               self.avatar_img = CTkImage(rounded, size=(40, 40))
               self.avatars[self.username] = self.avatar_img
               # Надіслати новий аватар на сервер
               with open(path, "rb") as f:
                   raw = f.read()
               import os
               b64_data = base64.b64encode(raw).decode()
               short_name = os.path.basename(path)
               avatar_data = f"AVATAR@{self.username}@{short_name}@{b64_data}\n"
               self.sock.sendall(avatar_data.encode())
               self.add_message("[SYSTEM] Ви змінили аватар.")
           except Exception as e:
               self.add_message(f"[Помилка зміни аватара] {e}")
   def users_listbox_right_click(self, event):
       try:
           index = self.users_listbox.index(f"@{event.x},{event.y}")
           user = self.users_listbox.get(f"{index} linestart", f"{index} lineend").strip()
           if not user or user == self.username:
               return
           from tkinter import Menu
           menu = Menu(self, tearoff=0)
           menu.add_command(label=f"Видалити {user}", command=lambda: self.kick_user(user))
           menu.tk_popup(event.x_root, event.y_root)
       except Exception:
           pass

   def kick_user(self, user):
       # Надіслати команду на сервер
       try:
           data = f"KICK@{user}\n"
           self.sock.sendall(data.encode())
       except Exception as e:
           self.add_message(f"[Помилка видалення] {e}")
   def __init__(self):
       super().__init__()
       self.avatars = {}  # Зберігаємо аватари інших користувачів (локально для кожного клієнта)
       self.geometry('700x800')
       self.title("💬 Modern Chat Client")
       set_appearance_mode("dark")
       set_default_color_theme("blue")
       self.username = None
       self.ask_username()
   def ask_username(self):
       self.avatar_path = None
       self.username_window = CTkToplevel(self)
       self.username_window.title("Введіть ім'я")
       self.username_window.geometry("370x220")
       self.username_window.grab_set()
       self.username_window.resizable(False, False)

       # Центрування вікна по екрану
       self.update_idletasks()
       x = self.winfo_x() + (self.winfo_width() // 2) - 185
       y = self.winfo_y() + (self.winfo_height() // 2) - 110
       self.username_window.geometry(f"370x220+{x}+{y}")

       frame = CTkFrame(self.username_window, fg_color="#23272f", corner_radius=16)
       frame.pack(expand=True, fill="both", padx=10, pady=10)
       CTkLabel(frame, text="Введіть ім'я для чату", font=('Segoe UI', 16, 'bold'), text_color="#60a5fa").pack(pady=(10, 4))
       self.username_entry = CTkEntry(frame, placeholder_text="Ваш нік...", font=('Segoe UI', 15), fg_color="#181c24", text_color="#e5e7eb", border_width=0, width=220, height=36)
       self.username_entry.pack(pady=4)
       self.username_entry.bind('<Return>', lambda e: self.set_username())

       # Аватар
       self.avatar_label = CTkLabel(frame, text="Аватар: (не обрано)", font=('Segoe UI', 13), text_color="#a1a1aa")
       self.avatar_label.pack(pady=(4, 2))
       CTkButton(frame, text="Обрати аватар", command=self.choose_avatar, fg_color="#374151", hover_color="#1e293b", text_color="#fbbf24", font=('Segoe UI', 13), corner_radius=8, width=140, height=32).pack(pady=(0, 6))

       CTkButton(frame, text="Увійти", command=self.set_username, fg_color="#2563eb", hover_color="#1e40af", text_color="white", font=('Segoe UI', 15, 'bold'), corner_radius=10, width=120, height=36).pack(pady=(4, 8))
       self.username_entry.focus_set()

   def choose_avatar(self):
       filetypes = [('Зображення', '*.png *.jpg *.jpeg *.gif *.bmp')]
       path = filedialog.askopenfilename(title='Оберіть аватар', filetypes=filetypes)
       if path:
           self.avatar_path = path
           import os
           self.avatar_label.configure(text=f"Аватар: {os.path.basename(path)}")

   def set_username(self):
       name = self.username_entry.get().strip()
       if name:
           self.username = name
           # Якщо обрано аватар, відправляємо його на сервер (base64)
           if self.avatar_path:
               try:
                   with open(self.avatar_path, "rb") as f:
                       raw = f.read()
                   b64_data = base64.b64encode(raw).decode()
                   short_name = os.path.basename(self.avatar_path)
                   # Надсилаємо аватар як спец. повідомлення
                   self._pending_avatar = (short_name, b64_data)
               except Exception as e:
                   self._pending_avatar = None
           else:
               self._pending_avatar = None
           self.username_window.destroy()
           self.show_chat()

   def show_chat(self):
       # Меню
       self.label = None
       self.menu_frame = CTkFrame(self, width=150, fg_color="#181c24", corner_radius=20, border_width=2, border_color="#2d3748")
       self.menu_frame.pack_propagate(False)
       self.menu_frame.place(x=0, y=0, relheight=1)
       # Список користувачів
       self.users_label = CTkLabel(self.menu_frame, text='У чаті:', font=('Segoe UI', 16, 'bold'), text_color="#60a5fa")
       self.users_label.pack(pady=(24,0), anchor="n")
       CTkButton(self.menu_frame, text="Змінити аватар", command=self.change_avatar, fg_color="#374151", hover_color="#1e293b", text_color="#fbbf24", font=('Segoe UI', 13), corner_radius=8, width=140, height=32).pack(pady=(0, 6))
       self.users_listbox = CTkTextbox(self.menu_frame, font=('Segoe UI', 13), fg_color="#23272f", text_color="#e5e7eb", border_width=0)
       self.users_listbox.pack(padx=16, pady=12, fill="both", expand=True)
       self.users_listbox.bind("<Button-3>", self.users_listbox_right_click)
       self.users = set()
       self.is_show_menu = False
       self.speed_animate_menu = -20

       # Основне поле чату
       self.chat_field = CTkScrollableFrame(self, width=550, height=500, fg_color="#23272f", corner_radius=20)
       self.chat_field.place(x=150, y=0)

       # Поле введення та кнопки (знизу)
       self.input_frame = CTkFrame(self, width=600, height=60, fg_color="#181c24", corner_radius=20, border_width=2, border_color="#2d3748")
       self.input_frame.place(x=0, y=640)
       self.input_label = CTkLabel(self.input_frame, text='Повідомлення:', font=('Segoe UI', 14), text_color="#60a5fa")
       self.input_label.place(x=0, y=10)
       self.message_entry = CTkEntry(self.input_frame, placeholder_text='Введіть повідомлення:', height=40, width=340, font=('Segoe UI', 14), fg_color="#23272f", text_color="#e5e7eb", border_width=0)
       self.message_entry.place(x=130, y=10)

       self.send_button = CTkButton(self.input_frame, text='>', width=50, height=40, command=self.send_message, fg_color="#2563eb", hover_color="#1e40af", text_color="white", font=('Segoe UI', 18, 'bold'), corner_radius=12)
       self.send_button.place(x=480, y=10)
       self.open_img_button = CTkButton(self.input_frame, text='📁', width=50, height=40, command=self.open_image, fg_color="#374151", hover_color="#1e293b", text_color="#fbbf24", font=('Segoe UI', 18), corner_radius=12)
       self.open_img_button.place(x=540, y=10)
       self.message_entry.bind('<Return>', lambda e: self.send_message())

       self.adaptive_ui()

       # Відображення аватарки користувача (якщо обрано)
       if self.avatar_path:
           try:
               pil_img = Image.open(self.avatar_path)
               rounded = make_rounded_avatar(pil_img, size=(40, 40))
               self.avatar_img = CTkImage(rounded, size=(40, 40))
               self.avatars[self.username] = self.avatar_img
           except Exception as e:
               self.avatar_img = None
               self.add_message(f"[Помилка аватара] {e}")
       else:
           self.avatar_img = None
           self.add_message(f"👤 Ваш нік: {self.username}")

       self.add_message("Демонстрація відображення зображення:",
                        CTkImage(Image.open('icon.jpg'), size=(320, 320)))

       try:
           self.sock = socket(AF_INET, SOCK_STREAM)
           self.sock.connect(('localhost', 8080))
           hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
           self.sock.send(hello.encode('utf-8'))
           # Якщо є аватар, надсилаємо його одразу після підключення
           if hasattr(self, '_pending_avatar') and self._pending_avatar:
               short_name, b64_data = self._pending_avatar
               avatar_data = f"AVATAR@{self.username}@{short_name}@{b64_data}\n"
               self.sock.sendall(avatar_data.encode())
           threading.Thread(target=self.recv_message, daemon=True).start()
       except Exception as e:
           self.add_message(f"Не вдалося підключитися до сервера: {e}")

   # def toggle_show_menu(self):
   #     if self.is_show_menu:
   #         self.is_show_menu = False
   #         self.speed_animate_menu *= -1
   #         self.btn.configure(text='▶️')
   #         self.show_menu()
   #     else:
   #         self.is_show_menu = True
   #         self.speed_animate_menu *= -1
   #         self.btn.configure(text='◀️')
   #         self.show_menu()
   #         # При відкритті меню – додамо приміром зміну імені
   #         self.label = CTkLabel(self.menu_frame, text='Імʼя')
   #         self.label.pack(pady=30)
   #         self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
   #         self.entry.pack()
   #         # Кнопка збереження
   #         self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
   #         self.save_button.pack()

   def show_menu(self):
       self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
       if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
           self.after(10, self.show_menu)
       elif self.menu_frame.winfo_width() >= 60 and not self.is_show_menu:
           self.after(10, self.show_menu)
           if self.label:
               self.label.destroy()
           if getattr(self, "entry", None):
               self.entry.destroy()
           if getattr(self, "save_button", None):
               self.save_button.destroy()

   def save_name(self):
       new_name = self.entry.get().strip()
       if new_name:
           self.username = new_name
           self.add_message(f"Ваш новий нік: {self.username}")

   def adaptive_ui(self):
       # Ліва панель "У чаті" завжди фіксована по висоті та не приховується
       self.menu_frame.place(x=0, y=0, relheight=1)
       self.menu_frame.configure(height=self.winfo_height())
       self.chat_field.place(x=150, y=0)
       self.chat_field.configure(width=self.winfo_width() - 150, height=self.winfo_height() - 80)
       y_input = self.winfo_height() - 70
       self.input_frame.place(x=150, y=y_input)
       self.input_label.place(x=0, y=10)
       self.message_entry.place(x=130, y=10)
       self.send_button.place(x=480, y=10)
       self.open_img_button.place(x=540, y=10)
       self.users_listbox.configure(height=self.menu_frame.winfo_height() - 100)
       self.after(50, self.adaptive_ui)
   def update_users_list(self):
       self.users_listbox.configure(state='normal')
       self.users_listbox.delete('1.0', 'end')
       for user in sorted(self.users):
           self.users_listbox.insert('end', user + '\n')
       self.users_listbox.configure(state='disabled')

   import datetime
   def add_message(self, message, img=None, author=None):
       # Відстеження користувачів за системними повідомленнями
       if '[SYSTEM]' in message:
           import re
           join_match = re.search(r'\[SYSTEM\] (.+?) приєднався', message)
           left_match = re.search(r'\[SYSTEM\] (.+?) вийшов', message)
           if join_match:
               self.users.add(join_match.group(1))
               self.update_users_list()
           elif left_match:
               left_user = left_match.group(1)
               if left_user in self.users:
                   self.users.discard(left_user)
                   self.update_users_list()
               # Додаємо окреме повідомлення у чат про вихід користувача (завжди, навіть якщо не було у списку)
               now = datetime.datetime.now().strftime("%H:%M")
               left_msg = f"{left_user} від'єднався(лась) з чату!  [{now}]"
               bubble_frame = CTkFrame(self.chat_field, fg_color="#b91c1c", corner_radius=15)
               bubble_frame.pack(pady=8, padx=10, anchor='w', fill='x')
               wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 100
               CTkLabel(bubble_frame, text=left_msg, wraplength=wrapleng_size,
                        text_color='white', justify='left', font=('Segoe UI', 14, 'italic')).pack(padx=16, pady=10, anchor='w')
               self.chat_field._parent_canvas.yview_moveto(1.0)
               return  # Не дублюємо системне повідомлення нижче

       is_me = (author == self.username) if author else (message.startswith(f"{self.username}:"))
       now = datetime.datetime.now().strftime("%H:%M")
       message_with_time = f"{message}  [{now}]"
       # Modern bubble style
       bg_color = '#2563eb' if is_me else '#23272f'
       text_color = 'white' if is_me else '#d1d5db'
       anchor = 'e' if is_me else 'w'
       bubble_frame = CTkFrame(self.chat_field, fg_color=bg_color, corner_radius=18)
       bubble_frame.pack(pady=10, padx=18, anchor=anchor, fill='x')
       wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 120

       # Відображення аватара для всіх користувачів
       avatar_img = None
       if author and author in self.avatars:
           avatar_img = self.avatars[author]
       elif is_me and hasattr(self, 'avatar_img') and self.avatar_img is not None:
           avatar_img = self.avatar_img

       if avatar_img:
           msg_frame = CTkFrame(bubble_frame, fg_color=bg_color)
           msg_frame.pack(fill='x', padx=0, pady=0)
           # Для своїх повідомлень аватар справа, для чужих — зліва
           if is_me:
               CTkLabel(msg_frame, image=avatar_img, text='', width=40, height=40).pack(side='right', padx=(0, 8), pady=4)
               CTkLabel(msg_frame, text=message_with_time, wraplength=wrapleng_size-60,
                        text_color=text_color, justify='left', font=('Segoe UI', 15)).pack(side='right', padx=(0, 0), pady=8)
           else:
               CTkLabel(msg_frame, image=avatar_img, text='', width=40, height=40).pack(side='left', padx=(0, 8), pady=4)
               CTkLabel(msg_frame, text=message_with_time, wraplength=wrapleng_size-60,
                        text_color=text_color, justify='left', font=('Segoe UI', 15)).pack(side='left', padx=(0, 0), pady=8)
       elif img:
           CTkLabel(bubble_frame, text=message_with_time, wraplength=wrapleng_size,
                    text_color=text_color, image=img, compound='top',
                    justify='left', font=('Segoe UI', 15)).pack(padx=20, pady=12, anchor=anchor)
       else:
           CTkLabel(bubble_frame, text=message_with_time, wraplength=wrapleng_size,
                    text_color=text_color, justify='left', font=('Segoe UI', 15)).pack(padx=20, pady=12, anchor=anchor)

       # Auto-scroll to bottom
       self.chat_field._parent_canvas.yview_moveto(1.0)

   def send_message(self):
       message = self.message_entry.get()
       if message:
           self.add_message(f"{self.username}: {message}", author=self.username)
           data = f"TEXT@{self.username}@{message}\n"
           try:
               self.sock.sendall(data.encode())
           except:
               pass
       self.message_entry.delete(0, END)

   def recv_message(self):
       buffer = ""
       while True:
           try:
               chunk = self.sock.recv(4096)
               if not chunk:
                   break
               buffer += chunk.decode('utf-8', errors='ignore')

               while "\n" in buffer:
                   line, buffer = buffer.split("\n", 1)
                   self.handle_line(line.strip())

           except:
               break
       self.sock.close()

   def handle_line(self, line):
       if not line:
           return
       parts = line.split("@", 3)
       msg_type = parts[0]

       if msg_type == "TEXT":
           if len(parts) >= 3:
               author = parts[1]
               message = parts[2]
               self.add_message(f"{author}: {message}", author=author)
       elif msg_type == "IMAGE":
           if len(parts) >= 4:
               author = parts[1]
               filename = parts[2]
               b64_img = parts[3]
               try:
                   img_data = base64.b64decode(b64_img)
                   pil_img = Image.open(io.BytesIO(img_data))
                   ctk_img = CTkImage(pil_img, size=(300, 300))
                   self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img, author=author)
               except Exception as e:
                   self.add_message(f"Помилка відображення зображення: {e}")
       elif msg_type == "AVATAR":
           # AVATAR@user@filename@base64
           if len(parts) >= 4:
               author = parts[1]
               filename = parts[2]
               b64_img = parts[3]
               try:
                   img_data = base64.b64decode(b64_img)
                   pil_img = Image.open(io.BytesIO(img_data))
                   rounded = make_rounded_avatar(pil_img, size=(40, 40))
                   avatar_img = CTkImage(rounded, size=(40, 40))
                   self.avatars[author] = avatar_img
               except Exception as e:
                   pass
       elif msg_type == "KICKED":
           # KICKED@user
           if len(parts) >= 2:
               kicked_user = parts[1]
               if kicked_user in self.users:
                   self.users.discard(kicked_user)
                   self.update_users_list()
               now = datetime.datetime.now().strftime("%H:%M")
               self.add_message(f"[SYSTEM] {kicked_user} був(ла) видалений(а) з чату!  [{now}]")
               # Якщо видалили мене — закрити клієнт
               if kicked_user == self.username:
                   self.after(1000, self.destroy)
       else:
           self.add_message(line)

   def open_image(self):
       file_name = filedialog.askopenfilename()
       if not file_name:
           return
       try:
           with open(file_name, "rb") as f:
               raw = f.read()
           b64_data = base64.b64encode(raw).decode()
           short_name = os.path.basename(file_name)
           data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
           self.sock.sendall(data.encode())
           self.add_message('', CTkImage(light_image=Image.open(file_name), size=(300, 300)))
       except Exception as e:
           self.add_message(f"Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
   win = MainWindow()
   win.mainloop()



