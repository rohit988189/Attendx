# database.py - UPDATED VERSION
import sqlite3
from datetime import datetime

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("attendance.db")
        create_tables(conn)  # Updated function name
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    return conn

def create_tables(conn):
    # Attendance table
    attendance_sql = """
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        lecture_id INTEGER,
        lecture_name TEXT,
        FOREIGN KEY (lecture_id) REFERENCES lectures(id)
    );
    """
    
    # Lectures table (NEW)
    lectures_sql = """
    CREATE TABLE IF NOT EXISTS lectures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecture_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1
    );
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(attendance_sql)
        cursor.execute(lectures_sql)
        conn.commit()
        
        # Insert sample lectures if none exist
        cursor.execute("SELECT COUNT(*) FROM lectures")
        if cursor.fetchone()[0] == 0:
            setup_sample_lectures(conn)
            
    except sqlite3.Error as e:
        print(f"Table creation error: {e}")

def setup_sample_lectures(conn):
    """Create sample lectures for testing"""
    lectures = [
        ("Morning Lecture", "09:00:00", "10:30:00"),
        ("Afternoon Lecture", "13:00:00", "14:30:00"),
        ("Evening Lecture", "16:00:00", "17:30:00")
    ]
    
    cursor = conn.cursor()
    for lecture_name, start_time, end_time in lectures:
        cursor.execute("""
            INSERT INTO lectures (lecture_name, start_time, end_time)
            VALUES (?, ?, ?)
        """, (lecture_name, start_time, end_time))
    conn.commit()

def mark_attendance(conn, name, lecture_id=None, lecture_name=None):
    today = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    
    # Check if already marked for this lecture today
    cursor = conn.cursor()
    if lecture_id:
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE name = ? AND date = ? AND lecture_id = ?
        """, (name, today, lecture_id))
    else:
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE name = ? AND date = ?
        """, (name, today))
    
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO attendance (name, date, time, lecture_id, lecture_name)
            VALUES (?, ?, ?, ?, ?)
        """, (name, today, time, lecture_id, lecture_name))
        conn.commit()
        print(f"Attendance marked for {name} in {lecture_name}")
        return True
    return False

# NEW FUNCTIONS FOR LECTURE MANAGEMENT
def get_current_lecture(conn):
    """Get the currently active lecture based on current time"""
    current_time = datetime.now().strftime("%H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM lectures 
        WHERE start_time <= ? AND end_time >= ? AND is_active = 1
        ORDER BY start_time
        LIMIT 1
    """, (current_time, current_time))
    
    return cursor.fetchone()

def create_lecture(conn, lecture_name, start_time, end_time):
    """Create a new lecture time period"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lectures (lecture_name, start_time, end_time)
        VALUES (?, ?, ?)
    """, (lecture_name, start_time, end_time))
    conn.commit()
    return cursor.lastrowid

def get_all_lectures(conn):
    """Get all lectures"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lectures ORDER BY start_time")
    return cursor.fetchall()

def get_todays_attendance(conn):
    """Get today's attendance records"""
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, date, time, lecture_name 
        FROM attendance 
        WHERE date = ? 
        ORDER BY time DESC 
        LIMIT 10
    """, (today,))
    return cursor.fetchall()
# Add these functions to your existing database.py

def get_attendance_by_lecture(conn, lecture_id=None):
    """Get attendance records filtered by lecture"""
    cursor = conn.cursor()
    
    if lecture_id:
        cursor.execute("""
            SELECT a.name, a.date, a.time, l.lecture_name 
            FROM attendance a 
            LEFT JOIN lectures l ON a.lecture_id = l.id 
            WHERE a.lecture_id = ?
            ORDER BY a.date DESC, a.time DESC
        """, (lecture_id,))
    else:
        cursor.execute("""
            SELECT a.name, a.date, a.time, l.lecture_name 
            FROM attendance a 
            LEFT JOIN lectures l ON a.lecture_id = l.id 
            ORDER BY a.date DESC, a.time DESC
        """)
    
    return cursor.fetchall()

def get_attendance_by_date_range(conn, start_date, end_date):
    """Get attendance records within a date range"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.name, a.date, a.time, l.lecture_name 
        FROM attendance a 
        LEFT JOIN lectures l ON a.lecture_id = l.id 
        WHERE a.date BETWEEN ? AND ?
        ORDER BY a.date DESC, a.time DESC
    """, (start_date, end_date))
    return cursor.fetchall()

def get_lecture_summary(conn):
    """Get summary of attendance by lecture"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            l.lecture_name,
            l.start_time,
            l.end_time,
            COUNT(DISTINCT a.name) as total_students,
            COUNT(a.id) as total_records,
            MAX(a.date) as last_activity
        FROM lectures l
        LEFT JOIN attendance a ON l.id = a.lecture_id
        GROUP BY l.id, l.lecture_name, l.start_time, l.end_time
        ORDER BY l.start_time
    """)
    return cursor.fetchall()

def get_student_attendance_summary(conn, student_name=None):
    """Get attendance summary for students"""
    cursor = conn.cursor()
    
    if student_name:
        cursor.execute("""
            SELECT 
                name,
                COUNT(DISTINCT date) as days_present,
                COUNT(DISTINCT lecture_id) as lectures_attended,
                GROUP_CONCAT(DISTINCT lecture_name) as attended_lectures
            FROM attendance 
            WHERE name = ?
            GROUP BY name
        """, (student_name,))
    else:
        cursor.execute("""
            SELECT 
                name,
                COUNT(DISTINCT date) as days_present,
                COUNT(DISTINCT lecture_id) as lectures_attended,
                GROUP_CONCAT(DISTINCT lecture_name) as attended_lectures
            FROM attendance 
            GROUP BY name
            ORDER BY name
        """)
    
    return cursor.fetchall()