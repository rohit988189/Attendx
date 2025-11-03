# register_users.py
import cv2
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import face_recognition
from datetime import datetime

class UserRegistration:
    def __init__(self, window):
        self.window = window
        self.window.title("User Registration")
        self.window.geometry("600x500")
        
        self.known_faces_dir = "known_faces"
        os.makedirs(self.known_faces_dir, exist_ok=True)
        
        # Initialize attributes
        self.total_samples = 1  # Only one image needed
        self.samples_captured = 0
        self.is_capturing = False
        self.current_user = ""
        
        self.setup_gui()
        self.cap = cv2.VideoCapture(0)
        
        # Check if camera opened successfully
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open camera. Please check if camera is connected and not being used by another application.")
            return
        
        self.update_video()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # User info frame
        info_frame = ttk.LabelFrame(main_frame, text="User Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="Full Name:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.name_entry = ttk.Entry(info_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(info_frame, text="User ID:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.id_entry = ttk.Entry(info_frame, width=30)
        self.id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Video frame
        video_frame = ttk.LabelFrame(main_frame, text="Camera Feed - Position face in the frame")
        video_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(padx=10, pady=10)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(main_frame, text="Instructions")
        instructions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        instructions_text = (
            "1. Enter Name and User ID\n"
            "2. Click 'Capture Photo'\n"
            "3. Ensure face is clearly visible in green box\n"
            "4. One clear photo will be saved for recognition"
        )
        ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        # Controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)
        
        self.btn_capture = ttk.Button(controls_frame, text="Capture Photo", 
                                     command=self.capture_single_photo)
        self.btn_capture.pack(side=tk.LEFT, padx=5)
        
        self.btn_retake = ttk.Button(controls_frame, text="Retake Photo", 
                                    command=self.retake_photo, state=tk.DISABLED)
        self.btn_retake.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready to capture", foreground="blue")
        self.status_label.pack()
        
        # Registered users frame
        users_frame = ttk.LabelFrame(main_frame, text="Registered Users")
        users_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.users_tree = ttk.Treeview(users_frame, columns=("Name", "ID"), 
                                      show="headings", height=8)
        self.users_tree.heading("Name", text="Name")
        self.users_tree.heading("ID", text="ID")
        
        self.users_tree.column("Name", width=200)
        self.users_tree.column("ID", width=150)
        
        scrollbar = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load existing users
        self.load_registered_users()
    
    def load_registered_users(self):
        # Clear existing entries
        for row in self.users_tree.get_children():
            self.users_tree.delete(row)
        
        # Get all registered users
        if os.path.exists(self.known_faces_dir):
            user_files = {}
            for filename in os.listdir(self.known_faces_dir):
                if filename.endswith('.jpg'):
                    # Extract user info from filename (format: userid_username.jpg)
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        user_id = parts[0]
                        username = parts[1].replace('.jpg', '')
                        user_files[user_id] = username
            
            # Add users to treeview
            for user_id, username in user_files.items():
                self.users_tree.insert("", tk.END, values=(username, user_id))
    
    def capture_single_photo(self):
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        if not name or not user_id:
            messagebox.showerror("Error", "Please enter both name and user ID")
            return
        
        # Check if user already exists
        existing_file = f"{user_id}_{name}.jpg"
        existing_path = os.path.join(self.known_faces_dir, existing_file)
        if os.path.exists(existing_path):
            if not messagebox.askyesno("User Exists", f"User '{name}' with ID '{user_id}' already exists. Overwrite?"):
                return
        
        # Clean the inputs for filename
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_')).rstrip()
        
        self.current_user = f"{clean_id}_{clean_name}"
        self.is_capturing = True
        
        self.btn_capture.config(state=tk.DISABLED)
        self.status_label.config(text="Looking for face... Position yourself clearly", foreground="orange")
        
        # Start face detection for single capture
        self.capture_face_once()
    
    def capture_face_once(self):
        """Capture a single clear face photo"""
        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                # Take the first detected face
                (x, y, w, h) = faces[0]
                
                # Draw green rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "Face Detected - Press 'Capture'", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Save the face immediately when detected
                face_img = frame[y:y+h, x:x+w]
                
                if face_img.size > 0:
                    filename = f"{self.current_user}.jpg"
                    filepath = os.path.join(self.known_faces_dir, filename)
                    cv2.imwrite(filepath, face_img)
                    
                    self.samples_captured = 1
                    self.is_capturing = False
                    
                    self.status_label.config(text=f"Photo captured successfully for {self.current_user.split('_')[1]}!", foreground="green")
                    self.btn_capture.config(state=tk.NORMAL)
                    self.btn_retake.config(state=tk.NORMAL)
                    
                    messagebox.showinfo("Success", f"Face photo captured successfully for {self.current_user.split('_')[1]}!")
                    self.load_registered_users()
                    return
            
            else:
                # No face detected
                self.status_label.config(text="No face detected. Please position face in camera view", foreground="red")
        
        # Continue looking for faces
        if self.is_capturing:
            self.window.after(100, self.capture_face_once)
    
    def retake_photo(self):
        """Allow user to retake the photo"""
        name = self.name_entry.get().strip()
        user_id = self.id_entry.get().strip()
        
        if not name or not user_id:
            messagebox.showerror("Error", "Please enter both name and user ID")
            return
        
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_')).rstrip()
        
        self.current_user = f"{clean_id}_{clean_name}"
        self.samples_captured = 0
        self.is_capturing = True
        
        self.btn_retake.config(state=tk.DISABLED)
        self.status_label.config(text="Retaking photo... Position face clearly", foreground="orange")
        
        # Delete previous photo if exists
        previous_file = f"{self.current_user}.jpg"
        previous_path = os.path.join(self.known_faces_dir, previous_file)
        if os.path.exists(previous_path):
            os.remove(previous_path)
        
        # Start new capture
        self.capture_face_once()
    
    def update_video(self):
        if hasattr(self, 'cap') and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Always show face detection boxes for guidance
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "Face Detected", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Display frame
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
        
        self.window.after(10, self.update_video)
    
    def on_close(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        self.window.destroy()

def simple_registration():
    """Simple command-line version for quick registration"""
    import cv2
    import os
    
    known_faces_dir = "known_faces"
    os.makedirs(known_faces_dir, exist_ok=True)
    
    name = input("Enter user's name: ").strip()
    user_id = input("Enter user ID: ").strip()
    
    if not name or not user_id:
        print("Error: Both name and user ID are required")
        return
    
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_')).rstrip()
    
    user_filename = f"{clean_id}_{clean_name}.jpg"
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print(f"Capturing face photo for {name}...")
    print("Position your face clearly in the camera and press Enter when ready")
    input("Press Enter to capture photo...")
    
    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_img = frame[y:y+h, x:x+w]
            
            if face_img.size > 0:
                filepath = os.path.join(known_faces_dir, user_filename)
                cv2.imwrite(filepath, face_img)
                print(f"Face photo saved successfully as {user_filename}")
            else:
                print("Error: Could not capture face image")
        else:
            print("Error: No face detected in the photo")
    else:
        print("Error: Could not capture photo")
    
    cap.release()

def quick_batch_registration():
    """Register multiple users quickly with single photos"""
    import cv2
    import os
    
    known_faces_dir = "known_faces"
    os.makedirs(known_faces_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("=== Quick Batch Registration ===")
    print("Register multiple users quickly. Type 'done' to finish.")
    
    while True:
        name = input("\nEnter user's name (or 'done' to finish): ").strip()
        if name.lower() == 'done':
            break
            
        user_id = input("Enter user ID: ").strip()
        
        if not name or not user_id:
            print("Error: Both name and user ID are required")
            continue
        
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_id = "".join(c for c in user_id if c.isalnum() or c in ('-', '_')).rstrip()
        
        user_filename = f"{clean_id}_{clean_name}.jpg"
        
        print(f"Capturing photo for {name}... Get ready!")
        input("Press Enter when ready to capture...")
        
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face_img = frame[y:y+h, x:x+w]
                
                if face_img.size > 0:
                    filepath = os.path.join(known_faces_dir, user_filename)
                    cv2.imwrite(filepath, face_img)
                    print(f"✓ Saved: {user_filename}")
                else:
                    print("✗ Error: Could not capture face image")
            else:
                print("✗ Error: No face detected")
        else:
            print("✗ Error: Could not capture photo")
    
    cap.release()
    print("Batch registration completed!")

if __name__ == "__main__":
    print("=== User Registration ===")
    print("1. GUI Registration (Recommended)")
    print("2. Command Line - Single User")
    print("3. Command Line - Multiple Users")
    
    choice = input("Choose option (1/2/3): ").strip()
    
    if choice == "1":
        try:
            window = tk.Tk()
            app = UserRegistration(window)
            window.protocol("WM_DELETE_WINDOW", app.on_close)
            window.mainloop()
        except Exception as e:
            print(f"GUI Error: {e}")
            print("Falling back to command line version...")
            simple_registration()
    elif choice == "2":
        simple_registration()
    elif choice == "3":
        quick_batch_registration()
    else:
        print("Invalid choice. Using command line single user...")
        simple_registration()