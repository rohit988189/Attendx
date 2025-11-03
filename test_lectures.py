# test_lectures.py
from database import create_connection, get_current_lecture
from datetime import datetime

def test_current_lecture():
    conn = create_connection()
    current_lecture = get_current_lecture(conn)
    
    if current_lecture:
        print(f"Current active lecture: {current_lecture[1]}")
        print(f"Time: {current_lecture[2]} - {current_lecture[3]}")
    else:
        print("No active lecture at this time")
        print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
    
    conn.close()

if __name__ == "__main__":
    test_current_lecture()