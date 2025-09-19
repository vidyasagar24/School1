from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# ---------------- Database Setup ----------------
def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
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

if __name__ == "__main__":
    app.run(debug=True)
