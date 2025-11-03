import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import face_recognition
import os
from PIL import Image, ImageTk
from database import create_connection, mark_attendance, get_current_lecture, get_todays_attendance, create_lecture, get_all_lectures

class AttendanceApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Smart Attendance System - Lecture Based")
        self.window.geometry("900x700")
        
        # Database connection
        self.conn = create_connection()
        
        # Load known faces
        self.known_encodings = []
        self.known_names = []
        self.load_known_faces()
        
        # GUI Components
        self.setup_gui()
        self.cap = cv2.VideoCapture(0)
        self.is_running = False
        self.update_video()
        self.update_lecture_status()
    
    def load_known_faces(self):
        self.known_encodings = []
        self.known_names = []

        for img_name in os.listdir("known_faces"):
            img_path = os.path.join("known_faces", img_name)
            image = face_recognition.load_image_file(img_path)
            
            encodings_list = face_recognition.face_encodings(image)
            
            if encodings_list:
                encoding = encodings_list[0]
                self.known_encodings.append(encoding)
                self.known_names.append(os.path.splitext(img_name)[0])
                print(f"Successfully loaded: {img_name}")
            else:
                print(f"ERROR: Could not find a face in {img_name}. Please use a clearer image.")
    
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left frame for video and controls
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Lecture status frame
        self.lecture_frame = ttk.LabelFrame(left_frame, text="Current Lecture Status")
        self.lecture_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.lecture_label = ttk.Label(self.lecture_frame, text="No active lecture", font=('Arial', 12, 'bold'))
        self.lecture_label.pack(pady=10)
        
        # Video frame
        self.video_frame = ttk.LabelFrame(left_frame, text="Live Camera Feed")
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(padx=10, pady=10)
        
        # Controls frame
        self.control_frame = ttk.Frame(left_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        self.btn_start = ttk.Button(
            self.control_frame, 
            text="Start Attendance", 
            command=self.start_attendance
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = ttk.Button(
            self.control_frame, 
            text="Stop Attendance", 
            command=self.stop_attendance
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        self.btn_register = ttk.Button(
            self.control_frame, 
            text="Register New User", 
            command=self.register_user
        )
        self.btn_register.pack(side=tk.LEFT, padx=5)
        
        self.btn_manage_lectures = ttk.Button(
            self.control_frame, 
            text="Manage Lectures", 
            command=self.manage_lectures
        )
        self.btn_manage_lectures.pack(side=tk.LEFT, padx=5)
        
        # NEW BUTTON: View Attendance
        self.btn_view_attendance = ttk.Button(
            self.control_frame, 
            text="View Attendance", 
            command=self.view_attendance
        )
        self.btn_view_attendance.pack(side=tk.LEFT, padx=5)
        
        # Right frame for attendance log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Attendance log
        self.log_frame = ttk.LabelFrame(right_frame, text="Today's Attendance Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Update treeview columns to include lecture name
        self.tree = ttk.Treeview(
            self.log_frame, 
            columns=("Name", "Time", "Lecture"), 
            show="headings"
        )
        self.tree.heading("Name", text="Name")
        self.tree.heading("Time", text="Time")
        self.tree.heading("Lecture", text="Lecture")
        
        self.tree.column("Name", width=120)
        self.tree.column("Time", width=100)
        self.tree.column("Lecture", width=150)
        
        scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial logs
        self.refresh_logs()
    
    def start_attendance(self):
        self.is_running = True
        current_lecture = get_current_lecture(self.conn)
        if current_lecture:
            messagebox.showinfo("Attendance Started", 
                              f"Attendance started for: {current_lecture[1]}\n"
                              f"Time: {current_lecture[2]} - {current_lecture[3]}")
        else:
            messagebox.showwarning("No Active Lecture", 
                                 "No lecture is currently scheduled. Attendance will not be marked.")
    
    def stop_attendance(self):
        self.is_running = False
        messagebox.showinfo("Attendance Stopped", "Attendance marking has been stopped.")
    
    def register_user(self):
        messagebox.showinfo("Info", "Use register_users.py to register new users.")
    
    def manage_lectures(self):
        # Open lecture management window
        LectureManager(tk.Toplevel(self.window), self.conn, self)
    
    # NEW METHOD: View Attendance
    def view_attendance(self):
        """Open the attendance viewer window"""
        from attendance_viewer import AttendanceViewer
        viewer_window = tk.Toplevel(self.window)
        viewer_window.title("Attendance Records Viewer")
        AttendanceViewer(viewer_window)
    
    def update_video(self):
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Face detection and recognition
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                # Get current active lecture
                current_lecture = get_current_lecture(self.conn)
                lecture_id = current_lecture[0] if current_lecture else None
                lecture_name = current_lecture[1] if current_lecture else "No Active Lecture"
                
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(
                        self.known_encodings, face_encoding, tolerance=0.5
                    )
                    name = "Unknown"
                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_names[first_match_index]
                        
                        # Only mark attendance if there's an active lecture
                        if lecture_id:
                            if mark_attendance(self.conn, name, lecture_id, lecture_name):
                                self.refresh_logs()
                                print(f"Attendance marked for {name} in {lecture_name}")
                        else:
                            print(f"No active lecture for {name}")
                    
                    # Scale coordinates
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    
                    # Draw bounding box and label
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, f"{name}", (left, top - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    cv2.putText(frame, f"Lecture: {lecture_name}", (left, bottom + 25), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Display frame in GUI
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.update_video)
    
    def update_lecture_status(self):
        """Update the lecture status display"""
        current_lecture = get_current_lecture(self.conn)
        if current_lecture:
            status_text = f"ACTIVE: {current_lecture[1]}\nTime: {current_lecture[2]} - {current_lecture[3]}"
            self.lecture_label.configure(text=status_text, foreground="green")
        else:
            self.lecture_label.configure(text="No active lecture\nAttendance will not be marked", foreground="red")
        
        # Update every 30 seconds
        self.window.after(30000, self.update_lecture_status)
    
    def refresh_logs(self):
        # Clear existing logs
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Fetch today's attendance data
        rows = get_todays_attendance(self.conn)
        
        for row in rows:
            self.tree.insert("", tk.END, values=(row[0], row[2], row[3]))
    
    def on_close(self):
        self.cap.release()
        self.conn.close()
        self.window.destroy()

class LectureManager:
    def __init__(self, window, conn, parent_app):
        self.window = window
        self.conn = conn
        self.parent_app = parent_app
        self.window.title("Lecture Manager")
        self.window.geometry("600x500")
        
        self.setup_gui()
        self.refresh_lectures()
    
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Lecture creation frame
        create_frame = ttk.LabelFrame(main_frame, text="Create New Lecture")
        create_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(create_frame, text="Lecture Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.lecture_name = ttk.Entry(create_frame, width=30)
        self.lecture_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(create_frame, text="Start Time (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.start_time = ttk.Entry(create_frame, width=30)
        self.start_time.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(create_frame, text="e.g., 09:00").grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(create_frame, text="End Time (HH:MM):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.end_time = ttk.Entry(create_frame, width=30)
        self.end_time.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(create_frame, text="e.g., 10:30").grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Button(create_frame, text="Create Lecture", 
                  command=self.create_lecture).grid(row=3, column=0, columnspan=3, pady=10)
        
        # Lectures list with delete functionality
        list_frame = ttk.LabelFrame(main_frame, text="Scheduled Lectures")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for lectures
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Start", "End", "Status"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Lecture Name")
        self.tree.heading("Start", text="Start Time")
        self.tree.heading("End", text="End Time")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("ID", width=40)
        self.tree.column("Name", width=150)
        self.tree.column("Start", width=80)
        self.tree.column("End", width=80)
        self.tree.column("Status", width=80)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons for lectures
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh List", 
                  command=self.refresh_lectures).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Delete Selected", 
                  command=self.delete_selected_lecture).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Delete All", 
                  command=self.delete_all_lectures).pack(side=tk.LEFT, padx=5)
    
    def create_lecture(self):
        name = self.lecture_name.get()
        start = self.start_time.get()
        end = self.end_time.get()
        
        if not all([name, start, end]):
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        # Add seconds to time if not provided
        if len(start) == 5:  # HH:MM format
            start += ":00"
        if len(end) == 5:    # HH:MM format
            end += ":00"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO lectures (lecture_name, start_time, end_time)
                VALUES (?, ?, ?)
            """, (name, start, end))
            self.conn.commit()
            messagebox.showinfo("Success", "Lecture created successfully!")
            self.refresh_lectures()
            self.parent_app.update_lecture_status()  # Update status in main app
            
            # Clear form
            self.lecture_name.delete(0, tk.END)
            self.start_time.delete(0, tk.END)
            self.end_time.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create lecture: {e}")
    
    def refresh_lectures(self):
        # Clear existing entries
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM lectures ORDER BY start_time")
        lectures = cursor.fetchall()
        
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        for lecture in lectures:
            # Determine if lecture is active
            start_time = lecture[2]
            end_time = lecture[3]
            is_active = start_time <= current_time <= end_time
            status = "Active" if is_active else "Inactive"
            
            self.tree.insert("", tk.END, values=(lecture[0], lecture[1], lecture[2], lecture[3], status))
    
    def delete_selected_lecture(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a lecture to delete")
            return
        
        lecture_id = self.tree.item(selection[0])['values'][0]
        lecture_name = self.tree.item(selection[0])['values'][1]
        
        # Check if there are attendance records for this lecture
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE lecture_id = ?", (lecture_id,))
        attendance_count = cursor.fetchone()[0]
        
        warning_msg = f"Delete lecture '{lecture_name}'?"
        if attendance_count > 0:
            warning_msg += f"\n\nWARNING: This lecture has {attendance_count} attendance records that will also be deleted!"
        
        if messagebox.askyesno("Confirm Delete", warning_msg):
            try:
                # Delete attendance records first (due to foreign key constraint)
                cursor.execute("DELETE FROM attendance WHERE lecture_id = ?", (lecture_id,))
                
                # Delete the lecture
                cursor.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
                self.conn.commit()
                
                messagebox.showinfo("Success", f"Lecture '{lecture_name}' deleted successfully!")
                self.refresh_lectures()
                self.parent_app.update_lecture_status()  # Update status in main app
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete lecture: {e}")
    
    def delete_all_lectures(self):
        # Check if there are any attendance records
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE lecture_id IS NOT NULL")
        attendance_count = cursor.fetchone()[0]
        
        warning_msg = "Delete ALL lectures?"
        if attendance_count > 0:
            warning_msg += f"\n\nWARNING: This will also delete {attendance_count} attendance records!"
        
        warning_msg += "\n\nThis action cannot be undone!"
        
        if messagebox.askyesno("DANGER", warning_msg):
            try:
                # Delete attendance records first
                cursor.execute("DELETE FROM attendance WHERE lecture_id IS NOT NULL")
                
                # Delete all lectures
                cursor.execute("DELETE FROM lectures")
                self.conn.commit()
                
                messagebox.showinfo("Success", "All lectures deleted successfully!")
                self.refresh_lectures()
                self.parent_app.update_lecture_status()  # Update status in main app
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete lectures: {e}")

if __name__ == "__main__":
    window = tk.Tk()
    app = AttendanceApp(window)
    window.protocol("WM_DELETE_WINDOW", app.on_close)
    window.mainloop()