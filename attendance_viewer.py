# attendance_viewer.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import create_connection, get_attendance_by_lecture, get_lecture_summary, get_attendance_by_date_range, get_student_attendance_summary, get_all_lectures
from datetime import datetime, timedelta

class AttendanceViewer:
    def __init__(self, window):
        self.window = window
        self.window.title("Attendance Viewer")
        self.window.geometry("1000x700")
        
        self.conn = create_connection()
        self.setup_gui()
        self.load_lectures()
        self.show_lecture_summary()
    
    def setup_gui(self):
        # Main notebook for different views
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Lecture Summary
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Lecture Summary")
        self.setup_summary_tab()
        
        # Tab 2: Detailed View
        self.detailed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.detailed_frame, text="Detailed Records")
        self.setup_detailed_tab()
        
        # Tab 3: Student Summary
        self.student_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.student_frame, text="Student Summary")
        self.setup_student_tab()
        
        # Tab 4: Date Range Filter
        self.date_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.date_frame, text="Date Range Filter")
        self.setup_date_tab()
    
    def setup_summary_tab(self):
        # Controls
        control_frame = ttk.Frame(self.summary_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Refresh Summary", 
                  command=self.show_lecture_summary).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Export to CSV", 
                  command=self.export_summary).pack(side=tk.LEFT, padx=5)
        
        # Summary treeview
        tree_frame = ttk.Frame(self.summary_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.summary_tree = ttk.Treeview(tree_frame, columns=("Lecture", "Time", "Students", "Records", "Last Activity"), show="headings")
        self.summary_tree.heading("Lecture", text="Lecture Name")
        self.summary_tree.heading("Time", text="Time Slot")
        self.summary_tree.heading("Students", text="Unique Students")
        self.summary_tree.heading("Records", text="Total Records")
        self.summary_tree.heading("Last Activity", text="Last Activity")
        
        self.summary_tree.column("Lecture", width=200)
        self.summary_tree.column("Time", width=150)
        self.summary_tree.column("Students", width=100)
        self.summary_tree.column("Records", width=100)
        self.summary_tree.column("Last Activity", width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)
        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double click to view details
        self.summary_tree.bind("<Double-1>", self.on_summary_double_click)
    
    def setup_detailed_tab(self):
        # Filter controls
        filter_frame = ttk.LabelFrame(self.detailed_frame, text="Filter by Lecture")
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Select Lecture:").grid(row=0, column=0, padx=5, pady=5)
        
        self.lecture_combo = ttk.Combobox(filter_frame, state="readonly", width=30)
        self.lecture_combo.grid(row=0, column=1, padx=5, pady=5)
        self.lecture_combo.bind('<<ComboboxSelected>>', self.on_lecture_selected)
        
        ttk.Button(filter_frame, text="Show All Records", 
                  command=self.show_all_records).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Export to CSV", 
                  command=self.export_detailed).grid(row=0, column=3, padx=5, pady=5)
        
        # Detailed records treeview
        tree_frame = ttk.Frame(self.detailed_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.detailed_tree = ttk.Treeview(tree_frame, columns=("Name", "Date", "Time", "Lecture"), show="headings")
        self.detailed_tree.heading("Name", text="Student Name")
        self.detailed_tree.heading("Date", text="Date")
        self.detailed_tree.heading("Time", text="Time")
        self.detailed_tree.heading("Lecture", text="Lecture")
        
        self.detailed_tree.column("Name", width=150)
        self.detailed_tree.column("Date", width=100)
        self.detailed_tree.column("Time", width=100)
        self.detailed_tree.column("Lecture", width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.detailed_tree.yview)
        self.detailed_tree.configure(yscrollcommand=scrollbar.set)
        self.detailed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_student_tab(self):
        # Student filter controls
        filter_frame = ttk.LabelFrame(self.student_frame, text="Student Filter")
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="Student Name:").grid(row=0, column=0, padx=5, pady=5)
        
        self.student_entry = ttk.Entry(filter_frame, width=30)
        self.student_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Search Student", 
                  command=self.search_student).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="Show All Students", 
                  command=self.show_all_students).grid(row=0, column=3, padx=5, pady=5)
        
        # Student summary treeview
        tree_frame = ttk.Frame(self.student_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.student_tree = ttk.Treeview(tree_frame, columns=("Name", "Days Present", "Lectures Attended", "Attended Lectures"), show="headings")
        self.student_tree.heading("Name", text="Student Name")
        self.student_tree.heading("Days Present", text="Days Present")
        self.student_tree.heading("Lectures Attended", text="Lectures Attended")
        self.student_tree.heading("Attended Lectures", text="Attended Lectures")
        
        self.student_tree.column("Name", width=150)
        self.student_tree.column("Days Present", width=100)
        self.student_tree.column("Lectures Attended", width=120)
        self.student_tree.column("Attended Lectures", width=300)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_date_tab(self):
        # Date range controls
        date_frame = ttk.LabelFrame(self.date_frame, text="Filter by Date Range")
        date_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(date_frame, text="From Date:").grid(row=0, column=0, padx=5, pady=5)
        self.from_date = ttk.Entry(date_frame, width=15)
        self.from_date.grid(row=0, column=1, padx=5, pady=5)
        self.from_date.insert(0, (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        
        ttk.Label(date_frame, text="To Date:").grid(row=0, column=2, padx=5, pady=5)
        self.to_date = ttk.Entry(date_frame, width=15)
        self.to_date.grid(row=0, column=3, padx=5, pady=5)
        self.to_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Button(date_frame, text="Filter by Date", 
                  command=self.filter_by_date).grid(row=0, column=4, padx=5, pady=5)
        
        ttk.Button(date_frame, text="Export to CSV", 
                  command=self.export_date_range).grid(row=0, column=5, padx=5, pady=5)
        
        # Date range treeview
        tree_frame = ttk.Frame(self.date_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.date_tree = ttk.Treeview(tree_frame, columns=("Name", "Date", "Time", "Lecture"), show="headings")
        self.date_tree.heading("Name", text="Student Name")
        self.date_tree.heading("Date", text="Date")
        self.date_tree.heading("Time", text="Time")
        self.date_tree.heading("Lecture", text="Lecture")
        
        self.date_tree.column("Name", width=150)
        self.date_tree.column("Date", width=100)
        self.date_tree.column("Time", width=100)
        self.date_tree.column("Lecture", width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.date_tree.yview)
        self.date_tree.configure(yscrollcommand=scrollbar.set)
        self.date_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_lectures(self):
        lectures = get_all_lectures(self.conn)
        lecture_names = ["All Lectures"] + [f"{lect[1]} ({lect[0]})" for lect in lectures]
        self.lecture_combo['values'] = lecture_names
        if lecture_names:
            self.lecture_combo.current(0)
    
    def show_lecture_summary(self):
        # Clear existing data
        for row in self.summary_tree.get_children():
            self.summary_tree.delete(row)
        
        summary = get_lecture_summary(self.conn)
        
        for row in summary:
            time_slot = f"{row[1]} - {row[2]}"
            students = row[3] if row[3] else 0
            records = row[4] if row[4] else 0
            last_activity = row[5] if row[5] else "No records"
            
            self.summary_tree.insert("", tk.END, values=(row[0], time_slot, students, records, last_activity))
    
    def on_summary_double_click(self, event):
        selection = self.summary_tree.selection()
        if selection:
            item = self.summary_tree.item(selection[0])
            lecture_name = item['values'][0]
            
            # Switch to detailed tab and filter by this lecture
            self.notebook.select(1)  # Switch to detailed tab
            
            # Find and select this lecture in the combo box
            for i, value in enumerate(self.lecture_combo['values']):
                if lecture_name in value:
                    self.lecture_combo.current(i)
                    self.on_lecture_selected(None)
                    break
    
    def on_lecture_selected(self, event):
        selected = self.lecture_combo.get()
        
        if selected == "All Lectures":
            self.show_all_records()
        else:
            # Extract lecture ID from the selection
            try:
                lecture_id = int(selected.split('(')[-1].rstrip(')'))
                self.show_lecture_records(lecture_id)
            except (ValueError, IndexError):
                messagebox.showerror("Error", "Could not parse lecture selection")
    
    def show_all_records(self):
        self.show_records_in_tree(self.detailed_tree, get_attendance_by_lecture(self.conn))
    
    def show_lecture_records(self, lecture_id):
        records = get_attendance_by_lecture(self.conn, lecture_id)
        self.show_records_in_tree(self.detailed_tree, records)
    
    def show_records_in_tree(self, tree, records):
        # Clear existing data
        for row in tree.get_children():
            tree.delete(row)
        
        for record in records:
            tree.insert("", tk.END, values=record)
    
    def search_student(self):
        student_name = self.student_entry.get().strip()
        if student_name:
            summary = get_student_attendance_summary(self.conn, student_name)
            self.show_student_summary(summary)
        else:
            messagebox.showwarning("Warning", "Please enter a student name")
    
    def show_all_students(self):
        summary = get_student_attendance_summary(self.conn)
        self.show_student_summary(summary)
    
    def show_student_summary(self, summary):
        # Clear existing data
        for row in self.student_tree.get_children():
            self.student_tree.delete(row)
        
        for row in summary:
            self.student_tree.insert("", tk.END, values=row)
    
    def filter_by_date(self):
        from_date = self.from_date.get().strip()
        to_date = self.to_date.get().strip()
        
        if from_date and to_date:
            try:
                records = get_attendance_by_date_range(self.conn, from_date, to_date)
                self.show_records_in_tree(self.date_tree, records)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid date format: {e}")
        else:
            messagebox.showwarning("Warning", "Please enter both from and to dates")
    
    def export_summary(self):
        self.export_to_csv(self.summary_tree, "lecture_summary.csv")
    
    def export_detailed(self):
        self.export_to_csv(self.detailed_tree, "detailed_attendance.csv")
    
    def export_date_range(self):
        self.export_to_csv(self.date_tree, "date_range_attendance.csv")
    
    def export_to_csv(self, tree, filename):
        try:
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write headers
                headers = [tree.heading(col)['text'] for col in tree['columns']]
                writer.writerow(headers)
                
                # Write data
                for row_id in tree.get_children():
                    row = tree.item(row_id)['values']
                    writer.writerow(row)
            
            messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

if __name__ == "__main__":
    window = tk.Tk()
    app = AttendanceViewer(window)
    window.mainloop()