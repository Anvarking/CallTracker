from werkzeug.security import check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv
import csv
from io import BytesIO, StringIO
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    session,
    Response,
    send_file
)
from openpyxl import Workbook
from database import (get_records,
                      add_record,
                      get_record_by_id,
                      update_plan_and_fact_by_id,
                      delete_record_by_id,
                      get_statistics,
                      get_completed_days,
                      get_failed_days,
                      get_chart_data,
                      get_progress,
                      get_export_records,
                      create_user,
                      get_user_by_username,
                      get_all_users,
                      delete_user,
                      toggle_user_status,
                      update_user,
                      get_user_by_id,
                      get_admin_count)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        if session.get("role") != "admin":
            flash(
                "❌ У вас нет прав для выполнения этого действия.",
                "danger"
            )
            return redirect("/")
        return func(*args, **kwargs)
    return wrapper

@app.route("/")
@login_required
def index():
    period = request.args.get("period", "all")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    records = get_records(
        period,
        date_from,
        date_to
    )
    statistics = get_statistics(
        period,
        date_from,
        date_to
    )
    completed_days = get_completed_days(
        period,
        date_from,
        date_to
    )
    failed_days = get_failed_days(
        period,
        date_from,
        date_to
    )
    chart_data = get_chart_data(
        period,
        date_from,
        date_to
    )
    progress = get_progress(
        period,
        date_from,
        date_to
    )
    return render_template(
        "index.html",
        records=records,
        statistics=statistics,
        completed_days=completed_days,
        failed_days=failed_days,
        chart_data=chart_data,
        progress=progress,
        period=period,
        date_from=date_from,
        date_to=date_to
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username)
        if (
            user
            and user[3]
            and check_password_hash(user[2], password)
        ):
            session["user_id"] = user[0]
            session["user"] = user[1]
            session["role"] = user[4]
            flash(
                "✅ Добро пожаловать!",
                "success"
            )
            return redirect("/")
        flash(
            "❌ Неверный логин или пароль.",
            "danger"
        )
    return render_template("login.html")

@app.route("/users")
@admin_required
def users():
    users = get_all_users()
    return render_template(
        "users.html",
        users=users
    )

@app.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    if request.method == "POST":
        username = request.form.get(
            "username",
            ""
        ).strip()
        password = request.form.get(
            "password",
            ""
        )
        role = request.form.get(
            "role",
            "user"
        )
        if not username or not password:
            flash(
                "❌ Заполните логин и пароль.",
                "danger"
            )
            return render_template(
                "add_user.html"
            )
        if role not in ("user", "admin"):
            flash(
                "❌ Некорректная роль.",
                "danger"
            )
            return render_template(
                "add_user.html"
            )
        result = create_user(
            username,
            password,
            role
        )
        if not result:
            flash(
                "❌ Пользователь с таким логином уже существует.",
                "warning"
            )
            return render_template(
                "add_user.html"
            )
        flash(
            f"✅ Пользователь {username} создан.",
            "success"
        )
        return redirect("/users")
    return render_template(
        "add_user.html"
    )

@app.route("/users/toggle/<int:id>", methods=["POST"])
@admin_required
def toggle_user(id):
    toggle_user_status(id)
    flash(
        "✅ Статус пользователя изменён.",
        "success"
    )
    return redirect("/users")

@app.route("/users/delete/<int:id>", methods=["POST"])
@admin_required
def remove_user(id):
    user = get_user_by_id(id)
    if not user:
        flash(
            "❌ Пользователь не найден.",
            "danger"
        )
        return redirect("/users")
    if user[2] == "admin":
        admin_count = get_admin_count()
        if admin_count <= 1:
            flash(
                "❌ Нельзя удалить последнего администратора.",
                "danger"
            )
            return redirect("/users")
    delete_user(id)
    flash(
        "✅ Пользователь удалён.",
        "success"
    )
    return redirect("/users")

@app.route("/users/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_user(id):
    user = get_user_by_id(id)
    if not user:
        flash(
            "❌ Пользователь не найден.",
            "danger"
        )
        return redirect("/users")
    if request.method == "POST":
        username = request.form.get(
            "username",
            ""
        ).strip()
        password = request.form.get(
            "password",
            ""
        )
        role = request.form.get(
            "role",
            "user"
        )
        if not username:
            flash(
                "❌ Логин не может быть пустым.",
                "danger"
            )
            return render_template(
                "edit_user.html",
                user=user
            )
        if role not in ("user", "admin"):
            flash(
                "❌ Некорректная роль.",
                "danger"
            )
            return render_template(
                "edit_user.html",
                user=user
            )
        if user[2] == "admin" and role != "admin":
            admin_count = get_admin_count()
            if admin_count <= 1:
                flash(
                    "❌ Нельзя убрать роль у последнего администратора.",
                    "danger"
                )
                return render_template(
                    "edit_user.html",
                    user=user
                )
        result = update_user(
            id,
            username,
            password,
            role
        )
        if not result:
            flash(
                "❌ Такой логин уже существует.",
                "warning"
            )
            return render_template(
                "edit_user.html",
                user=user
            )
        flash(
            "✅ Пользователь успешно изменён.",
            "success"
        )
        return redirect("/users")
    return render_template(
        "edit_user.html",
        user=user
    )

@app.route("/logout")
def logout():
    session.clear()
    flash(
        "👋 Вы вышли из системы.",
        "info"
    )
    return redirect("/login")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        date = request.form.get("date", "").strip()
        plan_raw = request.form.get("plan", "").strip()
        fact_raw = request.form.get("fact", "").strip()
        # Проверяем дату
        if not date:
            flash("❌ Выберите дату.", "danger")
            return render_template("add.html")
        # Проверяем пустые поля
        if not plan_raw or not fact_raw:
            flash("❌ Заполните план и факт.", "danger")
            return render_template("add.html")
        # Проверяем, что введены целые числа
        try:
            plan = int(plan_raw)
            fact = int(fact_raw)
        except ValueError:
            flash("❌ План и факт должны быть целыми числами.", "danger")
            return render_template("add.html")
        # Проверяем отрицательные значения
        if plan < 0 or fact < 0:
            flash("❌ Отрицательных значений быть не может.", "danger")
            return render_template("add.html")
        # Добавляем запись
        result = add_record(date, plan, fact)
        if not result:
            flash(
                f"❌ Запись за {date} уже существует.",
                "warning"
            )
            return render_template("add.html")
        flash("✅ Запись успешно добавлена.", "success")
        return redirect("/")
    return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    record = get_record_by_id(id)
    if request.method == "POST":
        plan_raw = request.form.get("plan", "").strip()
        fact_raw = request.form.get("fact", "").strip()
        # Проверяем, что поля не пустые
        if not plan_raw or not fact_raw:
            flash(
                "❌ Заполните план и факт.",
                "danger"
            )
            return render_template(
                "edit.html",
                record=record
            )
        # Проверяем, что введены целые числа
        try:
            plan = int(plan_raw)
            fact = int(fact_raw)
        except ValueError:
            flash(
                "❌ План и факт должны быть целыми числами.",
                "danger"
            )
            return render_template(
                "edit.html",
                record=record
            )
        # Проверяем отрицательные значения
        if plan < 0 or fact < 0:
            flash(
                "❌ Отрицательных значений быть не может.",
                "danger"
            )
            return render_template(
                "edit.html",
                record=record
            )
        # Обновляем запись
        update_plan_and_fact_by_id(id, plan, fact)
        flash(
            "✅ Запись успешно изменена.",
            "success"
        )
        return redirect("/")
    return render_template(
        "edit.html",
        record=record
    )

@app.route("/delete/<int:id>", methods=["GET", "POST"])
@admin_required
def delete(id):
    if request.method == "POST":
        delete_record_by_id(id)
        return redirect("/")
    record = get_record_by_id(id)
    return render_template("delete.html", record=record)

@app.route("/export/csv")
@login_required
def export_csv():
    period = request.args.get("period", "all")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    records = get_export_records(
        period,
        date_from,
        date_to
    )
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Дата",
        "План",
        "Факт",
        "Разница",
        "Выполнение"
    ])
    for record in records:
        writer.writerow([
            record[0],
            record[1],
            record[2],
            record[3],
            f"{record[4]}%"
        ])
    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )
    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=calltracker.csv"

    return response

@app.route("/export/excel")
@login_required
def export_excel():
    period = request.args.get("period", "all")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    records = get_export_records(
        period,
        date_from,
        date_to
    )
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "CallTracker"
    # Заголовки
    headers = [
        "Дата",
        "План",
        "Факт",
        "Разница",
        "Выполнение"
    ]
    worksheet.append(headers)
    # Данные
    for record in records:
        worksheet.append([
            record[0],
            record[1],
            record[2],
            record[3],
            float(record[4])
        ])
    # Ширина колонок
    worksheet.column_dimensions["A"].width = 15
    worksheet.column_dimensions["B"].width = 12
    worksheet.column_dimensions["C"].width = 12
    worksheet.column_dimensions["D"].width = 12
    worksheet.column_dimensions["E"].width = 15
    # Формат процентов
    for row in worksheet.iter_rows(
        min_row=2,
        min_col=5,
        max_col=5
    ):
        row[0].number_format = '0.00"%"'
    # Сохраняем в память
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="calltracker.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

if __name__ == "__main__":
    app.run(debug=True)