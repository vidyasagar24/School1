from flask import Flask, render_template, request, redirect, url_for, Response, send_file
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)

# Secret keyword for database export - CHANGE THIS!
EXPORT_PASSWORD = "admin123"  # Change this to your secure password

# ---------------- Database Setup ----------------
def get_db():
    conn = sqlite3.connect("school.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            fee REAL,
            dob TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- Routes ----------------
@app.route("/")
def index():
    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("index.html", students=students)

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        name = request.form["name"]
        student_class = request.form["class"]
        address = request.form["address"]
        phone = request.form["phone"]
        fee = request.form["fee"]
        dob = request.form["dob"]

        conn = get_db()
        conn.execute("INSERT INTO students (name, class, address, phone, fee, dob) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, student_class, address, phone, fee, dob))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        name = request.form["name"]
        student_class = request.form["class"]
        address = request.form["address"]
        phone = request.form["phone"]
        fee = request.form["fee"]
        dob = request.form["dob"]

        conn.execute("UPDATE students SET name=?, class=?, address=?, phone=?, fee=?, dob=? WHERE id=?",
                     (name, student_class, address, phone, fee, dob, id))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit.html", student=student)

@app.route("/delete/<int:id>")
def delete_student(id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/search", methods=["GET", "POST"])
def search_student():
    students = []
    if request.method == "POST":
        keyword = request.form["keyword"]
        conn = get_db()
        students = conn.execute("SELECT * FROM students WHERE name LIKE ? OR class LIKE ?", 
                                ('%' + keyword + '%', '%' + keyword + '%')).fetchall()
        conn.close()
    return render_template("search.html", students=students)

# ---------------- Export Routes ----------------
@app.route("/export", methods=["GET", "POST"])
def export_page():
    """Display the export page with password protection"""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == EXPORT_PASSWORD:
            # Password is correct, generate and download CSV
            return export_csv()
        else:
            error = "Incorrect password. Access denied."
    
    # For GET request or wrong password, show the form
    return render_template("export.html", error=error)

def export_csv():
    """Generate and return CSV file with all student data"""
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['ID', 'Name', 'Class', 'Address', 'Phone', 'Fee', 'Date of Birth']
    writer.writerow(headers)
    
    # Write student data
    for student in students:
        writer.writerow([
            student['id'],
            student['name'],
            student['class'],
            student['address'] or '',  # Handle NULL values
            student['phone'] or '',
            student['fee'] or '',
            student['dob'] or ''
        ])
    
    # Create the response
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"students_export_{timestamp}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

# ---------------- Alternative: Direct DB Download (Optional) ----------------
@app.route("/download-db", methods=["GET", "POST"])
def download_database():
    """Download the actual SQLite database file (also password protected)"""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == EXPORT_PASSWORD:
            # Password is correct, send the database file
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return send_file(
                    "school.db",
                    as_attachment=True,
                    download_name=f"school_backup_{timestamp}.db",
                    mimetype='application/x-sqlite3'
                )
            except FileNotFoundError:
                error = "Database file not found."
        else:
            error = "Incorrect password. Access denied."
    
    # Show password form
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Download Database</title></head>
    <body>
        <h2>Download Database File</h2>
        <form method="post">
            <label for="password">Enter Password:</label>
            <input type="password" name="password" id="password" required>
            <input type="submit" value="Download">
        </form>
        ''' + (f'<p style="color:red">{error}</p>' if error else '') + '''
        <br><a href="/">Back to Home</a>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)