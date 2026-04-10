from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS complaints(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        description TEXT,
        image TEXT,
        status TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",(username,password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login")
def login():
    return render_template("login_choice.html")

@app.route("/user_login", methods=["GET","POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        user = cur.fetchone()

        if user:
            session["user"] = username
            return redirect("/user_dashboard")

    return render_template("user_login.html")

@app.route("/user_dashboard", methods=["GET","POST"])
def user_dashboard():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        description = request.form["description"]
        file = request.files["image"]

        filename = file.filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO complaints (username,description,image,status) VALUES (?,?,?,?)",
                    (session["user"], description, filename, "Pending"))
        conn.commit()
        conn.close()

        return redirect("/user_dashboard")

    return render_template("user_dashboard.html")

@app.route("/view_status")
def view_status():
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM complaints WHERE username=?", (session["user"],))
    data = cur.fetchall()
    conn.close()

    return render_template("view_status.html", data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin":
            session["admin"] = True
            return redirect("/admin_dashboard")

    return render_template("admin_login.html")

@app.route("/admin_dashboard", methods=["GET","POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        search = request.form["search"]
        cur.execute("SELECT * FROM complaints WHERE username LIKE ?", ('%' + search + '%',))
    else:
        cur.execute("SELECT * FROM complaints")

    data = cur.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", data=data)

@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):
    if "admin" not in session:
        return redirect("/login")

    status = request.form["status"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE complaints SET status=? WHERE id=?", (status, id))
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")

# DELETE OPTION
@app.route("/delete_complaint/<int:id>")
def delete_complaint(id):
    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")

if __name__ == "__main__":
 app.run(debug=True)