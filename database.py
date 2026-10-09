import os

import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

def get_connection():
    connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        sslmode=os.getenv("DB_SSLMODE", "prefer"),
        options="-c search_path=public"
    )
    return connection

def create_user(username, password, role="user"):
    connection = get_connection()
    cursor = connection.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("""
            INSERT INTO users (
                username,
                password_hash,
                role
            )
            VALUES (%s, %s, %s)
        """, (
            username,
            password_hash,
            role
        ))
        connection.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def delete_user(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM users
        WHERE id = %s
    """, (user_id,))
    connection.commit()
    deleted_rows = cursor.rowcount
    cursor.close()
    connection.close()
    return deleted_rows

def toggle_user_status(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE users
        SET is_active = NOT is_active
        WHERE id = %s
    """, (user_id,))
    connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    connection.close()
    return updated_rows

def get_user_by_username(username):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            id,
            username,
            password_hash,
            is_active,
            role
        FROM users
        WHERE username = %s
    """, (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

def get_records(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT
            id,
            date,
            plan,
            fact,
            fact - plan AS difference,
            CASE
                WHEN plan = 0 THEN 0
                ELSE ROUND(fact * 100.0 / plan, 2)
            END AS percentage
        FROM daily_performance
        WHERE {date_filter}
        ORDER BY date;
    """, params)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

def add_record(date, plan, fact):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO daily_performance (date, plan, fact)
            VALUES (%s, %s, %s)
        """, (date, plan, fact))

        connection.commit()
        return True

    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        print(f"Запись за {date} уже существует!")
        return False

    finally:
        cursor.close()
        connection.close()

def update_fact(date, fact):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE daily_performance
        SET fact = %s
        WHERE date = %s
    """, (fact, date))

    connection.commit()

    updated_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return updated_rows

def update_plan(date, plan):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE daily_performance
        SET plan = %s
        WHERE date = %s
    """, (plan, date))

    connection.commit()

    updated_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return updated_rows

def update_plan_and_fact_by_id(id, plan, fact):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE daily_performance
        SET plan = %s,
            fact = %s
        WHERE id = %s
    """, (plan, fact, id))

    connection.commit()

    updated_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return updated_rows

def delete_record_by_id(id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM daily_performance
        WHERE id = %s
    """, (id,))

    connection.commit()

    deleted_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return deleted_rows

def get_best_worst_days():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            date,
            plan,
            fact,
            fact - plan AS difference,
            ROUND(fact * 100.0 / plan, 2) AS percentage
        FROM daily_performance
        WHERE plan != 0
        ORDER BY percentage DESC;
    """)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

def get_statistics(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT
            COUNT(*) AS working_days,
            SUM(plan) AS total_plan,
            SUM(fact) AS total_fact,
            SUM(fact - plan) AS total_difference,
            ROUND(AVG(fact), 2) AS average_fact,
            ROUND(AVG(fact * 100.0 / plan), 2) AS average_percentage
        FROM daily_performance
        WHERE plan != 0
          AND {date_filter};
    """, params)

    statistics = cursor.fetchone()

    cursor.close()
    connection.close()

    return statistics

def get_completed_days(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM daily_performance
        WHERE plan != 0
          AND fact >= plan
          AND {date_filter};
    """, params)

    completed_days = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return completed_days

def get_failed_days(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT COUNT(*)
        FROM daily_performance
        WHERE plan != 0
          AND fact < plan
          AND {date_filter};
    """, params)

    failed_days = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return failed_days

def get_record_by_id(id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, date, plan, fact
        FROM daily_performance
        WHERE id = %s
    """, (id,))

    record = cursor.fetchone()

    cursor.close()
    connection.close()

    return record

def get_chart_data(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT
            date,
            plan,
            fact
        FROM daily_performance
        WHERE {date_filter}
        ORDER BY date;
    """, params)

    chart_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return chart_data

def get_date_filter(period, date_from=None, date_to=None):

    if period == "custom":
        return (
            "date BETWEEN %s AND %s",
            (date_from, date_to)
        )

    return (
        "TRUE",
        ()
    )

def get_progress(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()
    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )
    cursor.execute(f"""
        SELECT
            COALESCE(SUM(plan), 0),
            COALESCE(SUM(fact), 0)
        FROM daily_performance
        WHERE plan != 0
          AND {date_filter};
    """, params)
    progress = cursor.fetchone()
    cursor.close()
    connection.close()
    total_plan = progress[0]
    total_fact = progress[1]
    if total_plan == 0:
        percentage = 0
    else:
        percentage = round(
            total_fact * 100 / total_plan,
            2
        )

    return total_plan, total_fact, percentage

def get_export_records(
    period="all",
    date_from=None,
    date_to=None
):
    connection = get_connection()
    cursor = connection.cursor()

    date_filter, params = get_date_filter(
        period,
        date_from,
        date_to
    )

    cursor.execute(f"""
        SELECT
            date,
            plan,
            fact,
            fact - plan AS difference,
            CASE
                WHEN plan = 0 THEN 0
                ELSE ROUND(fact * 100.0 / plan, 2)
            END AS percentage
        FROM daily_performance
        WHERE {date_filter}
        ORDER BY date;
    """, params)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records

def get_all_users():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            id,
            username,
            role,
            is_active,
            created_at
        FROM users
        ORDER BY id;
    """)
    users = cursor.fetchall()
    cursor.close()
    connection.close()

    return users

def update_user(user_id, username, password, role):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if password:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE users
                SET username = %s,
                    password_hash = %s,
                    role = %s
                WHERE id = %s
            """, (
                username,
                password_hash,
                role,
                user_id
            ))
        else:
            cursor.execute("""
                UPDATE users
                SET username = %s,
                    role = %s
                WHERE id = %s
            """, (
                username,
                role,
                user_id
            ))
        connection.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()

def get_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            id,
            username,
            role,
            is_active
        FROM users
        WHERE id = %s
    """, (user_id,))

    user = cursor.fetchone()
    cursor.close()
    connection.close()

    return user

def get_admin_count():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'admin'
          AND is_active = TRUE
    """)
    admin_count = cursor.fetchone()[0]
    cursor.close()
    connection.close()

    return admin_count

