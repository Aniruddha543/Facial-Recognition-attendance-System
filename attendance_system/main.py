import csv
import datetime
import hashlib
import cv2
import os
import face_recognition
import numpy as np
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from reportlab.lib.pagesizes import letter
from kivy.graphics import Color, Rectangle

import time
import threading
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from Crypto.Cipher import AES
import base64

from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.core.window import Window

logged_in_enrollment = None  # Global variable to store logged-in student's enrollment number


# Utility function for hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to verify student credentials
def verify_student_credentials(enrollment, password):
    try:
        with open('student_data.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == enrollment and row[1] == hash_password(password):
                    return True
    except FileNotFoundError:
        pass
    return False

# Assuming you have a CSV file or database to store the attendance


def mark_attendance(student_enrollment):
    # Define the path to your attendance CSV file
    attendance_file = 'attendance.csv'

    # Open the attendance file in append mode
    with open(attendance_file, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Write the attendance record: student enrollment and the current date and time
        writer.writerow([student_enrollment, str(datetime.datetime.now())])

    print(f"Attendance marked for {student_enrollment}")


# Function to load stored face encodings
def load_face_encodings():
    face_encodings = {}
    try:
        with open('face_data.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                enrollment, encoding_str = row[0], row[1]
                encoding = np.fromstring(encoding_str[1:-1], sep=',')
                face_encodings[enrollment] = encoding
    except FileNotFoundError:
        pass
    return face_encodings

# Function to recognize face and mark attendance
def load_face_encodings():
    """Load face encodings from face_data.csv"""
    face_encodings = {}
    try:
        with open('face_data.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                enrollment, encoding_str = row[0], row[1]
                encoding = np.fromstring(encoding_str[1:-1], sep=',')  # Convert string to numpy array
                face_encodings[enrollment] = encoding
    except FileNotFoundError:
        pass
    return face_encodings

def recognize_face():
    """Recognize the face and mark attendance for the correct enrollment number."""
    known_faces = load_face_encodings()

    if not known_faces:
        return "No registered faces found!"

    if logged_in_enrollment is None:
        return "No student logged in!"

    cap = cv2.VideoCapture(0)
    success, frame = cap.read()
    cap.release()

    if not success:
        return "Error capturing image"

    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    if not face_encodings:
        return "No face detected! Please try again."

    best_match = None
    best_distance = float('inf')  # Set initial distance to a high value

    for face_encoding in face_encodings:
        for enrollment, known_encoding in known_faces.items():
            distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
            if distance < 0.4 and distance < best_distance:  # Threshold for strong match
                best_match = enrollment
                best_distance = distance

    if best_match == logged_in_enrollment:  # Ensure that only the logged-in student can mark attendance
        mark_attendance(best_match)
        return f"Attendance marked for {best_match}"
    else:
        return "Face not recognized! Try again."

# Screen 1: Main Menu

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title_label = Label(
            text="Attendance System",
            font_size=30,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=80
        )

        login_btn = Button(
            text='Student Login',
            font_size=20,
            size_hint_y=None,
            height=70,
            background_color=(0, 0.5, 1, 1),
            on_press=self.goto_student_login
        )
        
        manage_btn = Button(
            text='Management',
            font_size=20,
            size_hint_y=None,
            height=70,
            background_color=(0, 0.5, 1, 1),
            on_press=self.goto_management
        )
        
        logs_btn = Button(
            text='View Logs',
            font_size=20,
            size_hint_y=None,
            height=70,
            background_color=(0, 0.5, 1, 1),
            on_press=self.goto_logs
        )

        exit_btn = Button(
            text='Exit',
            font_size=20,
            size_hint_y=None,
            height=70,
            background_color=(1, 0, 0, 1),
            on_press=lambda instance: App.get_running_app().stop()
        )

        layout.add_widget(title_label)
        layout.add_widget(login_btn)
        layout.add_widget(manage_btn)
        layout.add_widget(logs_btn)
        layout.add_widget(exit_btn)
        
        self.add_widget(layout)

    def goto_student_login(self, instance):
        self.manager.current = 'student_login'

    def goto_management(self, instance):
        self.manager.current = 'management'

    def goto_logs(self, instance):
        self.manager.current = 'logs'

# Screen 2: Student Login


class StudentLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title_label = Label(
            text='Student Login',
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        self.enrollment_input = TextInput(
            hint_text='Enter Enrollment Number',
            font_size=18,
            size_hint_y=None,
            height=50
        )

        self.password_input = TextInput(
            hint_text='Enter Password',
            password=True,
            font_size=18,
            size_hint_y=None,
            height=50
        )

        login_btn = Button(
            text='Login',
            font_size=20,
            background_color=(0, 0.5, 1, 1),
            size_hint_y=None,
            height=70,
            on_press=self.verify_student
        )

        self.status_label = Label(
            text='',
            font_size=18,
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=30
        )

        back_btn = Button(
            text='Back',
            font_size=18,
            background_color=(1, 0, 0, 1),
            size_hint_y=None,
            height=60,
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(self.enrollment_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        layout.add_widget(self.status_label)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def verify_student(self, instance):
        enrollment = self.enrollment_input.text
        password = self.password_input.text

        if verify_student_credentials(enrollment, password):
            global logged_in_enrollment
            logged_in_enrollment = enrollment
            self.status_label.text = "Login Successful"
            self.status_label.color = (0, 1, 0, 1)

            # ✅ Clear login fields before moving to the next screen
            self.enrollment_input.text = ""
            self.password_input.text = ""

            self.manager.current = 'start_attendance'
        else:
            self.status_label.text = "Invalid Credentials"
            self.status_label.color = (1, 0, 0, 1)

    def go_back(self, instance):
        # ✅ Clear login fields when going back as well
        self.enrollment_input.text = ""
        self.password_input.text = ""
        self.manager.current = 'main_menu'
# Screen 3: Start Attendance

class StartAttendanceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title_label = Label(
            text='Start Attendance',
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        instruction_label = Label(
            text='Press the button below to capture your face for attendance.',
            font_size=18,
            size_hint_y=None,
            height=50
        )

        start_btn = Button(
            text='Capture Face for Attendance',
            font_size=20,
            background_color=(0, 0.5, 1, 1),
            size_hint_y=None,
            height=70,
            on_press=self.start_attendance
        )

        back_btn = Button(
            text='Back',
            font_size=18,
            background_color=(1, 0, 0, 1),
            size_hint_y=None,
            height=60,
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(instruction_label)
        layout.add_widget(start_btn)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def start_attendance(self, instance):
        if logged_in_enrollment is None:
            result = "No student logged in!"
            self.manager.get_screen('attendance_done').status_label.text = result
            self.manager.current = 'attendance_done'
            return

        cap = cv2.VideoCapture(0)
        recognized = False

        for _ in range(5):  # Try for a few frames to detect face
            ret, frame = cap.read()
            if not ret:
                break
            face_locations = face_recognition.face_locations(frame)
            if face_locations:
                recognized = self.verify_logged_in_student(frame)
                break
            time.sleep(0.5)

        cap.release()
        
        if recognized:
            self.open_live_feed()
        else:
            self.manager.get_screen('attendance_done').status_label.text = "Face not recognized or not matching logged-in student!"
            self.manager.current = 'attendance_done'

    def verify_logged_in_student(self, frame):
        known_faces = self.load_face_encodings()
        if logged_in_enrollment not in known_faces:
            return False
        
        face_encoding = face_recognition.face_encodings(frame)[0]
        match = face_recognition.compare_faces([known_faces[logged_in_enrollment]], face_encoding)[0]
        return match


    def open_live_feed(self):
        cap = cv2.VideoCapture(0)
        start_time = time.time()
        start_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))

        known_faces = self.load_face_encodings()
        if logged_in_enrollment not in known_faces:
            print("Logged-in student face encoding not found.")
            cap.release()
            return

        logged_in_encoding = known_faces[logged_in_enrollment]

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("Live Attendance Monitoring", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame)

            if not face_encodings:
                # No face in frame
                if time.time() - start_time > 10:
                    end_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    self.save_attendance_log(logged_in_enrollment, start_timestamp, end_timestamp)
                    print("Student moved out. Logging out...")
                    cap.release()
                    cv2.destroyAllWindows()
                    self.manager.current = 'student_login'
                    return
            else:
                match = face_recognition.compare_faces([logged_in_encoding], face_encodings[0])[0]
                if not match:
                    # Unauthorized face detected
                    end_timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    self.save_attendance_log(logged_in_enrollment, start_timestamp, end_timestamp)
                    print("⚠️ Unauthorized face detected. Ending session...")
                    cap.release()
                    cv2.destroyAllWindows()
                    self.manager.get_screen('attendance_done').status_label.text = "⚠️ Another face detected! Logging out..."
                    self.manager.current = 'attendance_done'
                    return
                else:
                    # Reset timer because logged-in student is still present
                    start_time = time.time()

        cap.release()
        cv2.destroyAllWindows()

    def load_face_encodings(self):
        face_encodings = {}
        try:
            with open('face_data.csv', 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    enrollment, encoding_str = row[0], row[1]
                    encoding = np.fromstring(encoding_str[1:-1], sep=',')
                    face_encodings[enrollment] = encoding
        except FileNotFoundError:
            pass
        return face_encodings


    def save_attendance_log(self, enrollment, start_time, end_time):
        with open('attendance_logs.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([enrollment, start_time, end_time])

    def go_back(self, instance):
        self.manager.current = 'student_login'

# Screen 4: Attendance Done

class AttendanceDoneScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title_label = Label(
            text='Attendance Status',
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        self.status_label = Label(
            text='',
            font_size=20,
            color=(0, 0.5, 1, 1),
            size_hint_y=None,
            height=50
        )

        back_btn = Button(
            text='Back',
            font_size=18,
            background_color=(1, 0, 0, 1),
            size_hint_y=None,
            height=60,
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(self.status_label)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = 'start_attendance'  # Go back to the start attendance screen

# Screen 5: Management - Login

class ManagementLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title_label = Label(
            text='Management Login',
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        self.username_input = TextInput(
            hint_text='Enter Username',
            font_size=18,
            size_hint_y=None,
            height=50
        )

        self.password_input = TextInput(
            hint_text='Enter Password',
            password=True,
            font_size=18,
            size_hint_y=None,
            height=50
        )

        self.status_label = Label(
            text='',
            font_size=18,
            color=(1, 0, 0, 1),  # Red color for error messages
            size_hint_y=None,
            height=40
        )

        login_btn = Button(
            text='Login',
            font_size=18,
            background_color=(0, 0.5, 1, 1),  # Blue button
            size_hint_y=None,
            height=60,
            on_press=self.verify_management
        )

        back_btn = Button(
            text='Back',
            font_size=18,
            background_color=(1, 0, 0, 1),  # Red button for navigation
            size_hint_y=None,
            height=60,
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        layout.add_widget(self.status_label)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def verify_management(self, instance):
        if self.username_input.text == "SUBHADIP" and self.password_input.text == "1234":
            self.status_label.text = "[color=00FF00]Login Successful[/color]"
            self.status_label.markup = True  # Enable colored text
            self.manager.current = 'register_student'  # Navigate to register student screen

            # ✅ Clear login information after moving to the next screen
            self.username_input.text = ""
            self.password_input.text = ""
            
        else:
            self.status_label.text = "[color=FF0000]Invalid Credentials[/color]"
            self.status_label.markup = True  # Enable colored text

    def go_back(self, instance):
        self.manager.current = 'main_menu'  # Navigate back to the main menu

# Screen 6: Register New Student

class RegisterStudentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title_label = Label(
            text='Register New Student',
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        self.enrollment_input = TextInput(
            hint_text='Enter Enrollment Number',
            font_size=18,
            size_hint_y=None,
            height=50
        )

        self.password_input = TextInput(
            hint_text='Enter Password',
            password=True,
            font_size=18,
            size_hint_y=None,
            height=50
        )

        register_btn = Button(
            text='Register Student',
            font_size=20,
            background_color=(0, 0.5, 1, 1),
            size_hint_y=None,
            height=70,
            on_press=self.register_student
        )

        self.status_label = Label(
            text='',
            font_size=18,
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=30
        )

        back_btn = Button(
            text='Back',
            font_size=18,
            background_color=(1, 0, 0, 1),
            size_hint_y=None,
            height=60,
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(self.enrollment_input)
        layout.add_widget(self.password_input)
        layout.add_widget(register_btn)
        layout.add_widget(self.status_label)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def register_student(self, instance):
        enrollment = self.enrollment_input.text.strip()
        password = self.password_input.text.strip()

        if not enrollment or not password:
            self.status_label.text = "Please enter both Enrollment Number and Password"
            return

        students = self.load_student_data()
        existing_enrollments = [row[0] for row in students]

        if enrollment in existing_enrollments:
            self.status_label.text = "Enrollment number already exists!"
            return

        hashed_password = hash_password(password)

        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            cv2.imshow("Press 'C' to capture face", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c'):
                face_locations = face_recognition.face_locations(frame)
                if face_locations:
                    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
                    self.save_face_data(enrollment, face_encoding)
                    print(f"✅ Face captured for {enrollment}")
                else:
                    self.status_label.text = "No face detected! Try again."
                    return
                break

        cap.release()
        cv2.destroyAllWindows()

        students.append([enrollment, hashed_password])
        with open('student_data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(students)

        self.status_label.text = "✅ Student Registered Successfully"

    def load_student_data(self):
        try:
            with open('student_data.csv', 'r') as file:
                reader = csv.reader(file)
                return [row for row in reader]
        except FileNotFoundError:
            return []

    def save_face_data(self, enrollment, face_encoding):
        face_data = self.load_face_encodings()
        face_data[enrollment] = face_encoding

        with open('face_data.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for enr, enc in face_data.items():
                writer.writerow([enr, np.array2string(enc, separator=',')])

    def load_face_encodings(self):
        face_encodings = {}
        try:
            with open('face_data.csv', 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    enrollment, encoding_str = row[0], row[1]
                    encoding = np.fromstring(encoding_str[1:-1], sep=',')
                    face_encodings[enrollment] = encoding
        except FileNotFoundError:
            pass
        return face_encodings

    def go_back(self, instance):
        self.manager.current = 'management'

# Screen 7: Logs

class LogsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        title_label = Label(
            text="Attendance Logs",
            font_size=26,
            bold=True,
            size_hint_y=None,
            height=50
        )

        self.logs_label = Label(
            text="Logs will appear here",
            font_size=16,
            halign="left",
            valign="top",
            size_hint_y=None
        )

        # Scrollable View for Logs
        scroll_view = ScrollView(size_hint=(1, 0.6))
        grid = GridLayout(cols=1, size_hint_y=None)
        grid.add_widget(self.logs_label)
        scroll_view.add_widget(grid)

        self.refresh_button = Button(
            text="Refresh Logs",
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(0, 0.5, 1, 1),
            on_press=self.refresh_logs
        )

        self.export_button = Button(
            text="Export to PDF",
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(0, 0.7, 0, 1),
            on_press=self.export_to_pdf
        )

        self.back_button = Button(
            text="Back",
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(1, 0, 0, 1),
            on_press=self.go_back
        )

        layout.add_widget(title_label)
        layout.add_widget(scroll_view)
        layout.add_widget(self.refresh_button)
        layout.add_widget(self.export_button)
        layout.add_widget(self.back_button)

        self.add_widget(layout)

        # ✅ Load logs when the screen is initialized
        self.refresh_logs(None)

    def get_attendance_logs(self):
        """Load attendance logs from CSV with Start and End Time."""
        attendance_data = []

        try:
            with open('attendance_logs.csv', mode='r') as file:
                reader = csv.reader(file)
                
                for row in reader:
                    if len(row) >= 3:  # Ensure Start Time & End Time exist
                        student_enrollment, start_time, end_time = row[:3]
                        attendance_data.append((student_enrollment, start_time, end_time))
        except FileNotFoundError:
            print("⚠️ Attendance log file not found. No data to display.")

        return attendance_data

    def refresh_logs(self, instance):
        """Refresh logs displayed on the screen."""
        logs = self.get_attendance_logs()

        if not logs:
            self.logs_label.text = "No attendance records found."
            return

        log_text = "📜 **Attendance Records:**\n"
        for log in logs:
            enrollment, start_time, end_time = log
            log_text += f"[b]{enrollment}[/b] - {start_time} → {end_time}\n"

        self.logs_label.text = log_text
        self.logs_label.markup = True  # Enable bold text

    def export_to_pdf(self, instance):
        """Exports attendance records to a PDF file and saves it."""

        logs = self.get_attendance_logs()
        filename = f"attendance_record_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf"
        save_path = os.path.join(os.getcwd(), filename)

        c = canvas.Canvas(save_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Attendance Record")
        c.drawString(100, 730, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")

        y = 700
        for student in logs:
            c.drawString(100, y, f"{student[0]} - {student[1]} → {student[2]}")
            y -= 20

        c.save()

        # Show a popup confirmation
        self.show_popup(f"✅ PDF exported successfully!\n📂 Saved at: {save_path}")

    def show_popup(self, message):
        """Display a popup notification."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=message, font_size=16)
        close_button = Button(text="Close", size_hint_y=None, height=50, on_press=lambda x: popup.dismiss())

        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)

        popup = Popup(title="Export Status", content=popup_layout, size_hint=(0.8, 0.4))
        popup.open()

    def go_back(self, instance):
        """Navigate back to the main menu."""
        self.manager.current = 'main_menu'# Screen Manager

# Attendance App

class AttendanceApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(StudentLoginScreen(name='student_login'))
        sm.add_widget(StartAttendanceScreen(name='start_attendance'))
        sm.add_widget(AttendanceDoneScreen(name='attendance_done'))
        sm.add_widget(ManagementLoginScreen(name='management'))
        sm.add_widget(RegisterStudentScreen(name='register_student'))
        sm.add_widget(LogsScreen(name='logs'))
        # adding new
        sm.add_widget(StudentLoginScreen(name='student_login'))
        sm.add_widget(ManagementLoginScreen(name='management'))
        sm.add_widget(LogsScreen(name='view_logs'))  # Assuming you renamed it to LogsScreen
        
        return sm

if __name__ == '__main__':
    AttendanceApp().run()
