import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DB = "expenses.db"
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Health", "Other"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )"""
        )


@app.route("/")
def index():
    db = get_db()
    category = request.args.get("category", "")
    month = request.args.get("month", "")  # format YYYY-MM
    edit_id = request.args.get("edit", type=int)

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if month:
        query += " AND substr(date, 1, 7) = ?"
        params.append(month)
    query += " ORDER BY date DESC, id DESC"
    expenses = db.execute(query, params).fetchall()

    total = sum(e["amount"] for e in expenses)

    summary_query = "SELECT category, SUM(amount) AS total FROM expenses WHERE 1=1"
    summary_params = []
    if month:
        summary_query += " AND substr(date, 1, 7) = ?"
        summary_params.append(month)
    summary_query += " GROUP BY category ORDER BY total DESC"
    summary = db.execute(summary_query, summary_params).fetchall()
    max_total = max((s["total"] for s in summary), default=1)

    editing = None
    if edit_id:
        editing = db.execute("SELECT * FROM expenses WHERE id = ?", (edit_id,)).fetchone()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        summary=summary,
        max_total=max_total,
        categories=CATEGORIES,
        selected_category=category,
        selected_month=month,
        editing=editing,
        today=date.today().isoformat(),
    )


@app.route("/add", methods=["POST"])
def add():
    db = get_db()
    db.execute(
        "INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)",
        (
            request.form["title"].strip(),
            float(request.form["amount"]),
            request.form["category"],
            request.form["date"],
        ),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/update/<int:expense_id>", methods=["POST"])
def update(expense_id):
    db = get_db()
    db.execute(
        "UPDATE expenses SET title = ?, amount = ?, category = ?, date = ? WHERE id = ?",
        (
            request.form["title"].strip(),
            float(request.form["amount"]),
            request.form["category"],
            request.form["date"],
            expense_id,
        ),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    db = get_db()
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
