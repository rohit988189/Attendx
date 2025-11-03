# delete_entries.py
import sys
import os
import sqlite3

def command_line_delete():
    """Command-line version for quick deletions"""
    conn = sqlite3.connect("attendance.db")
    
    while True:
        print("\n" + "="*50)
        print("        DATA MANAGEMENT - COMMAND LINE")
        print("="*50)
        print("1. Delete all entries")
        print("2. Delete entries by name")
        print("3. Delete entries by date")
        print("4. View database statistics")
        print("5. Exit")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                # First check if there are any records
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM attendance")
                total_records = cursor.fetchone()[0]
                
                if total_records == 0:
                    print("❌ No records found in the database!")
                    continue
                    
                confirm = input(f"Are you sure you want to delete ALL {total_records} entries? (yes/no): ")
                if confirm.lower() == 'yes':
                    cursor.execute("DELETE FROM attendance")
                    conn.commit()
                    print("✓ All entries deleted!")
                else:
                    print("✗ Operation cancelled")
            
            elif choice == "2":
                name = input("Enter name to delete: ").strip()
                if name:
                    cursor = conn.cursor()
                    # First check if records exist for this name
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE name = ?", (name,))
                    record_count = cursor.fetchone()[0]
                    
                    if record_count == 0:
                        print(f"❌ No records found for name: {name}")
                    else:
                        confirm = input(f"Delete {record_count} records for '{name}'? (yes/no): ")
                        if confirm.lower() == 'yes':
                            cursor.execute("DELETE FROM attendance WHERE name = ?", (name,))
                            conn.commit()
                            print(f"✓ Deleted {record_count} records for {name}")
                        else:
                            print("✗ Operation cancelled")
                else:
                    print("✗ No name provided")
            
            elif choice == "3":
                date = input("Enter date (YYYY-MM-DD): ").strip()
                if date:
                    cursor = conn.cursor()
                    # First check if records exist for this date
                    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (date,))
                    record_count = cursor.fetchone()[0]
                    
                    if record_count == 0:
                        print(f"❌ No records found for date: {date}")
                    else:
                        confirm = input(f"Delete {record_count} records for date '{date}'? (yes/no): ")
                        if confirm.lower() == 'yes':
                            cursor.execute("DELETE FROM attendance WHERE date = ?", (date,))
                            conn.commit()
                            print(f"✓ Deleted {record_count} records for {date}")
                        else:
                            print("✗ Operation cancelled")
                else:
                    print("✗ No date provided")
            
            elif choice == "4":
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM attendance")
                total = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT name) FROM attendance")
                unique = cursor.fetchone()[0]
                cursor.execute("SELECT MIN(date), MAX(date) FROM attendance")
                date_range = cursor.fetchone()
                
                print(f"\n--- Database Statistics ---")
                print(f"Total records: {total}")
                print(f"Unique students: {unique}")
                if date_range[0]:
                    print(f"Date range: {date_range[0]} to {date_range[1]}")
                else:
                    print("Date range: No records")
            
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("✗ Invalid choice! Please enter 1-5")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            break
        except Exception as e:
            print(f"✗ Error: {e}")
    
    conn.close()

def run_gui_version():
    """Run the GUI version - completely separate function"""
    import tkinter as tk
    from tkinter import ttk, messagebox
    from datetime import datetime, timedelta

    class DeleteManager:
        def __init__(self, window):
            self.window = window
            self.window.title("Data Management")
            self.window.geometry("800x600")
            
            self.conn = sqlite3.connect("attendance.db")
            self.setup_gui()
            self.load_statistics()
        
        def setup_gui(self):
            # Main notebook for different delete operations
            self.notebook = ttk.Notebook(self.window)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Tab 1: Delete Attendance Records
            self.attendance_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.attendance_frame, text="Attendance Records")
            self.setup_attendance_tab()
            
            # Tab 2: Delete Users
            self.users_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.users_frame, text="User Management")
            self.setup_users_tab()
            
            # Tab 3: Database Maintenance
            self.maintenance_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.maintenance_frame, text="Database Maintenance")
            self.setup_maintenance_tab()
        
        def setup_attendance_tab(self):
            # Statistics frame
            stats_frame = ttk.LabelFrame(self.attendance_frame, text="Database Statistics")
            stats_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.stats_label = ttk.Label(stats_frame, text="Loading statistics...")
            self.stats_label.pack(pady=10)
            
            # Delete by name
            name_frame = ttk.LabelFrame(self.attendance_frame, text="Delete by Student Name")
            name_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(name_frame, text="Student Name:").grid(row=0, column=0, padx=5, pady=5)
            self.name_entry = ttk.Entry(name_frame, width=30)
            self.name_entry.grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Button(name_frame, text="Delete All Records for Student", 
                      command=self.delete_by_name).grid(row=0, column=2, padx=5, pady=5)
            
            # Delete by date
            date_frame = ttk.LabelFrame(self.attendance_frame, text="Delete by Date")
            date_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(date_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
            self.date_entry = ttk.Entry(date_frame, width=15)
            self.date_entry.grid(row=0, column=1, padx=5, pady=5)
            self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            ttk.Button(date_frame, text="Delete Records for Date", 
                      command=self.delete_by_date).grid(row=0, column=2, padx=5, pady=5)
            
            # Delete by date range
            range_frame = ttk.LabelFrame(self.attendance_frame, text="Delete by Date Range")
            range_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(range_frame, text="From:").grid(row=0, column=0, padx=5, pady=5)
            self.from_date = ttk.Entry(range_frame, width=15)
            self.from_date.grid(row=0, column=1, padx=5, pady=5)
            self.from_date.insert(0, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
            
            ttk.Label(range_frame, text="To:").grid(row=0, column=2, padx=5, pady=5)
            self.to_date = ttk.Entry(range_frame, width=15)
            self.to_date.grid(row=0, column=3, padx=5, pady=5)
            self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            ttk.Button(range_frame, text="Delete Records in Range", 
                      command=self.delete_by_date_range).grid(row=0, column=4, padx=5, pady=5)
            
            # Bulk operations
            bulk_frame = ttk.LabelFrame(self.attendance_frame, text="Bulk Operations")
            bulk_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(bulk_frame, text="Delete ALL Attendance Records", 
                      command=self.delete_all_attendance).pack(pady=10)
        
        def setup_users_tab(self):
            # Registered users list
            users_frame = ttk.LabelFrame(self.users_frame, text="Registered Users")
            users_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.users_tree = ttk.Treeview(users_frame, columns=("UserID", "Samples"), show="headings")
            self.users_tree.heading("UserID", text="User ID")
            self.users_tree.heading("Samples", text="Face Samples")
            
            self.users_tree.column("UserID", width=200)
            self.users_tree.column("Samples", width=100)
            
            scrollbar = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
            self.users_tree.configure(yscrollcommand=scrollbar.set)
            self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # User operations frame
            user_ops_frame = ttk.Frame(self.users_frame)
            user_ops_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(user_ops_frame, text="Refresh Users List", 
                      command=self.load_users).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(user_ops_frame, text="Delete Selected User", 
                      command=self.delete_selected_user).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(user_ops_frame, text="Delete ALL Users", 
                      command=self.delete_all_users).pack(side=tk.LEFT, padx=5)
            
            # Load users initially
            self.load_users()
        
        def setup_maintenance_tab(self):
            # Database info
            info_frame = ttk.LabelFrame(self.maintenance_frame, text="Database Information")
            info_frame.pack(fill=tk.X, padx=10, pady=10)
            
            self.db_info_label = ttk.Label(info_frame, text="")
            self.db_info_label.pack(pady=10)
            
            # Maintenance operations
            ops_frame = ttk.LabelFrame(self.maintenance_frame, text="Maintenance Operations")
            ops_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(ops_frame, text="Optimize Database", 
                      command=self.optimize_database).pack(pady=5)
            
            ttk.Button(ops_frame, text="Backup Database", 
                      command=self.backup_database).pack(pady=5)
            
            ttk.Button(ops_frame, text="Reset Entire System", 
                      command=self.reset_system).pack(pady=10)
            
            # Load database info
            self.load_database_info()
        
        def load_statistics(self):
            cursor = self.conn.cursor()
            
            # Get total records
            cursor.execute("SELECT COUNT(*) FROM attendance")
            total_records = cursor.fetchone()[0]
            
            # Get unique students
            cursor.execute("SELECT COUNT(DISTINCT name) FROM attendance")
            unique_students = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("SELECT MIN(date), MAX(date) FROM attendance")
            date_range = cursor.fetchone()
            
            stats_text = f"Total Records: {total_records} | Unique Students: {unique_students}"
            if date_range[0]:
                stats_text += f" | Date Range: {date_range[0]} to {date_range[1]}"
            
            self.stats_label.config(text=stats_text)
        
        def load_users(self):
            # Clear existing entries
            for row in self.users_tree.get_children():
                self.users_tree.delete(row)
            
            # Count samples for each user
            user_samples = {}
            known_faces_dir = "known_faces"
            if os.path.exists(known_faces_dir):
                for filename in os.listdir(known_faces_dir):
                    if filename.endswith('.jpg'):
                        user_id = filename.split('_')[0]
                        if user_id in user_samples:
                            user_samples[user_id] += 1
                        else:
                            user_samples[user_id] = 1
            
            # Add users to treeview
            for user_id, samples in user_samples.items():
                self.users_tree.insert("", tk.END, values=(user_id, samples))
            
            # Show message if no users found
            if not user_samples:
                self.users_tree.insert("", tk.END, values=("No users found", "0"))
        
        def load_database_info(self):
            cursor = self.conn.cursor()
            
            # Get database size
            db_size = os.path.getsize("attendance.db") if os.path.exists("attendance.db") else 0
            db_size_mb = db_size / (1024 * 1024)
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            info_text = f"Database Size: {db_size_mb:.2f} MB\nTables: {', '.join([table[0] for table in tables])}"
            self.db_info_label.config(text=info_text)
        
        def delete_by_name(self):
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a student name")
                return
            
            cursor = self.conn.cursor()
            # First check if records exist
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE name = ?", (name,))
            record_count = cursor.fetchone()[0]
            
            if record_count == 0:
                messagebox.showinfo("No Records", f"No attendance records found for student: {name}")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Delete {record_count} attendance records for '{name}'?"):
                cursor.execute("DELETE FROM attendance WHERE name = ?", (name,))
                self.conn.commit()
                messagebox.showinfo("Success", f"Deleted {record_count} records for {name}")
                self.load_statistics()
        
        def delete_by_date(self):
            date = self.date_entry.get().strip()
            if not date:
                messagebox.showerror("Error", "Please enter a date")
                return
            
            cursor = self.conn.cursor()
            # First check if records exist
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (date,))
            record_count = cursor.fetchone()[0]
            
            if record_count == 0:
                messagebox.showinfo("No Records", f"No attendance records found for date: {date}")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Delete {record_count} attendance records for date '{date}'?"):
                cursor.execute("DELETE FROM attendance WHERE date = ?", (date,))
                self.conn.commit()
                messagebox.showinfo("Success", f"Deleted {record_count} records for {date}")
                self.load_statistics()
        
        def delete_by_date_range(self):
            from_date = self.from_date.get().strip()
            to_date = self.to_date.get().strip()
            
            if not from_date or not to_date:
                messagebox.showerror("Error", "Please enter both from and to dates")
                return
            
            cursor = self.conn.cursor()
            # First check if records exist
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date BETWEEN ? AND ?", (from_date, to_date))
            record_count = cursor.fetchone()[0]
            
            if record_count == 0:
                messagebox.showinfo("No Records", f"No attendance records found between {from_date} and {to_date}")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Delete {record_count} attendance records from {from_date} to {to_date}?"):
                cursor.execute("DELETE FROM attendance WHERE date BETWEEN ? AND ?", (from_date, to_date))
                self.conn.commit()
                messagebox.showinfo("Success", f"Deleted {record_count} records from {from_date} to {to_date}")
                self.load_statistics()
        
        def delete_all_attendance(self):
            cursor = self.conn.cursor()
            # First check if records exist
            cursor.execute("SELECT COUNT(*) FROM attendance")
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                messagebox.showinfo("No Records", "No attendance records found in the database!")
                return
            
            if messagebox.askyesno("DANGER", f"This will delete ALL {total_records} attendance records. This action cannot be undone!\n\nAre you absolutely sure?"):
                cursor.execute("DELETE FROM attendance")
                self.conn.commit()
                messagebox.showinfo("Success", f"Deleted all {total_records} attendance records")
                self.load_statistics()
        
        def delete_selected_user(self):
            selection = self.users_tree.selection()
            if not selection:
                messagebox.showerror("Error", "Please select a user to delete")
                return
            
            user_id = self.users_tree.item(selection[0])['values'][0]
            
            # Check if it's the "No users found" placeholder
            if user_id == "No users found":
                messagebox.showinfo("No Users", "No users found to delete")
                return
            
            # Check if user has any attendance records
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE name = ?", (user_id,))
            attendance_count = cursor.fetchone()[0]
            
            # Check if user has face samples
            face_samples_exist = False
            known_faces_dir = "known_faces"
            if os.path.exists(known_faces_dir):
                user_files = [f for f in os.listdir(known_faces_dir) if f.startswith(user_id + '_')]
                face_samples_exist = len(user_files) > 0
            
            if not face_samples_exist and attendance_count == 0:
                messagebox.showinfo("No Data", f"No face samples or attendance records found for user: {user_id}")
                return
            
            confirmation_msg = f"Delete user '{user_id}'?"
            if face_samples_exist:
                confirmation_msg += f"\n- Will remove face samples"
            if attendance_count > 0:
                confirmation_msg += f"\n- Will delete {attendance_count} attendance records"
            
            if messagebox.askyesno("Confirm Delete", confirmation_msg):
                # Delete face samples
                if face_samples_exist:
                    for filename in os.listdir(known_faces_dir):
                        if filename.startswith(user_id + '_'):
                            os.remove(os.path.join(known_faces_dir, filename))
                
                # Delete attendance records
                if attendance_count > 0:
                    cursor.execute("DELETE FROM attendance WHERE name = ?", (user_id,))
                    self.conn.commit()
                
                messagebox.showinfo("Success", f"Deleted user '{user_id}'")
                self.load_users()
                self.load_statistics()
        
        def delete_all_users(self):
            # Check if any users exist
            known_faces_dir = "known_faces"
            if not os.path.exists(known_faces_dir) or not os.listdir(known_faces_dir):
                messagebox.showinfo("No Users", "No users found to delete")
                return
            
            if messagebox.askyesno("DANGER", "This will delete ALL users and their face samples. This action cannot be undone!\n\nAre you absolutely sure?"):
                # Delete all face samples
                known_faces_dir = "known_faces"
                if os.path.exists(known_faces_dir):
                    for filename in os.listdir(known_faces_dir):
                        os.remove(os.path.join(known_faces_dir, filename))
                
                messagebox.showinfo("Success", "Deleted all users and face samples")
                self.load_users()
        
        def optimize_database(self):
            cursor = self.conn.cursor()
            cursor.execute("VACUUM")
            self.conn.commit()
            messagebox.showinfo("Success", "Database optimized successfully")
            self.load_database_info()
        
        def backup_database(self):
            import shutil
            from datetime import datetime
            
            backup_name = f"attendance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2("attendance.db", backup_name)
            messagebox.showinfo("Success", f"Database backed up as {backup_name}")
        
        def reset_system(self):
            # Check if there's anything to reset
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM attendance")
            attendance_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM lectures")
            lecture_count = cursor.fetchone()[0]
            
            known_faces_dir = "known_faces"
            user_count = 0
            if os.path.exists(known_faces_dir):
                user_count = len([f for f in os.listdir(known_faces_dir) if f.endswith('.jpg')])
            
            if attendance_count == 0 and lecture_count == 0 and user_count == 0:
                messagebox.showinfo("No Data", "No data found to reset. The system is already empty.")
                return
            
            if messagebox.askyesno("DANGER", "This will COMPLETELY RESET the entire system:\n\n"
                                           f"- Delete {attendance_count} attendance records\n"
                                           f"- Delete {lecture_count} lecture schedules\n"
                                           f"- Delete {user_count} user face samples\n\n"
                                           "This action cannot be undone!\n\n"
                                           "Are you absolutely sure?"):
                # Delete attendance records
                cursor.execute("DELETE FROM attendance")
                cursor.execute("DELETE FROM lectures")
                self.conn.commit()
                
                # Delete face samples
                known_faces_dir = "known_faces"
                if os.path.exists(known_faces_dir):
                    for filename in os.listdir(known_faces_dir):
                        os.remove(os.path.join(known_faces_dir, filename))
                
                messagebox.showinfo("Success", "System reset complete. All data has been deleted.")
                self.load_statistics()
                self.load_users()
                self.load_database_info()
        
        def on_close(self):
            self.conn.close()
            self.window.destroy()
    
    # Create and run the GUI
    window = tk.Tk()
    app = DeleteManager(window)
    window.protocol("WM_DELETE_WINDOW", app.on_close)
    window.mainloop()

if __name__ == "__main__":
    # Simple choice - completely separate the two versions
    print("="*50)
    print("    ATTENDANCE SYSTEM - DATA MANAGEMENT")
    print("="*50)
    print("1. GUI (Graphical Interface)")
    print("2. Command Line (Terminal)")
    print()
    
    try:
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "1":
            print("Starting GUI version...")
            run_gui_version()
        else:
            print("Starting command line version...")
            command_line_delete()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Starting command line version...")
        command_line_delete()