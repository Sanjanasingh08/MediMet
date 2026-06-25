from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = "medicine123"

# ---------------- MySQL Configuration ---------------- #

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "medicine_reminder"

mysql = MySQL(app)

# ---------------- Home ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- Register ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, password)
        )

        mysql.connection.commit()
        cur.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- Login ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cur.fetchone()

        cur.close()

        if user:

            session["user_id"] = user[0]
            session["name"] = user[1]

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid Email or Password"
        )

    return render_template("login.html")


# ---------------- Dashboard ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")
    status = request.args.get("status", "All")

    cur = mysql.connection.cursor()

    query = """
    SELECT * FROM medicines
    WHERE user_id=%s
    """

    values = [session["user_id"]]

    if search:
        query += " AND medicine_name LIKE %s"
        values.append("%" + search + "%")

    if status != "All":
        query += " AND status=%s"
        values.append(status)

    cur.execute(query, tuple(values))

    medicines = cur.fetchall()

    cur.execute(
        "SELECT COUNT(*) FROM medicines WHERE user_id=%s",
        (session["user_id"],)
    )

    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM medicines WHERE user_id=%s AND status='Pending'",
        (session["user_id"],)
    )

    pending = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM medicines WHERE user_id=%s AND status='Taken'",
        (session["user_id"],)
    )

    taken = cur.fetchone()[0]

    cur.close()

    return render_template(
        "dashboard.html",
        name=session["name"],
        medicines=medicines,
        search=search,
        status=status,
        total=total,
        pending=pending,
        taken=taken
    )


# ---------------- Add Medicine ---------------- #

@app.route("/add_medicine", methods=["GET", "POST"])
def add_medicine():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        medicine_name = request.form["medicine_name"]
        dosage = request.form["dosage"]
        reminder_time = request.form["reminder_time"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO medicines
        (user_id, medicine_name, dosage,
        reminder_time, start_date, end_date)

        VALUES(%s,%s,%s,%s,%s,%s)
        """,
        (
            session["user_id"],
            medicine_name,
            dosage,
            reminder_time,
            start_date,
            end_date
        ))

        mysql.connection.commit()

        cur.close()

        return redirect("/dashboard")

    return render_template("add_medicine.html")


# ---------------- Delete ---------------- #

@app.route("/delete/<int:id>")
def delete(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM medicines WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect("/dashboard")


# ---------------- Taken ---------------- #

@app.route("/taken/<int:id>")
def taken(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "UPDATE medicines SET status='Taken' WHERE id=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect("/dashboard")


# ---------------- Edit ---------------- #

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    cur = mysql.connection.cursor()

    if request.method == "POST":

        cur.execute("""

        UPDATE medicines

        SET medicine_name=%s,

        dosage=%s,

        reminder_time=%s,

        start_date=%s,

        end_date=%s

        WHERE id=%s

        """,

        (

            request.form["medicine_name"],

            request.form["dosage"],

            request.form["reminder_time"],

            request.form["start_date"],

            request.form["end_date"],

            id

        ))

        mysql.connection.commit()

        cur.close()

        return redirect("/dashboard")

    cur.execute(
        "SELECT * FROM medicines WHERE id=%s",
        (id,)
    )

    medicine = cur.fetchone()

    cur.close()

    return render_template(
        "edit_medicine.html",
        medicine=medicine
    )


# ---------------- Logout ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)