"""Модуль для работы с базой данных."""

import os
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    """Создает подключение к базе данных."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        msg = "DATABASE_URL не установлен!"
        raise ValueError(msg)
    return psycopg2.connect(database_url)


def add_url(name):
    """
    Добавляет новый URL в базу данных.

    Args:
        name: Нормализованный URL

    Returns:
        ID созданной записи или None если URL уже существует
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id FROM urls WHERE name = %s", (name,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        return None

    created_at = datetime.now(tz=timezone.utc)
    cur.execute(
        "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
        (name, created_at),
    )
    url_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()

    return url_id


def get_url_by_name(name):
    """Получает URL по имени."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM urls WHERE name = %s", (name,))
    url = cur.fetchone()
    cur.close()
    conn.close()
    return url


def get_url_by_id(url_id):
    """Получает URL по ID."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
    url = cur.fetchone()
    cur.close()
    conn.close()
    return url


def get_all_urls():
    """Получает все URLs c информацией о последней проверке."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            urls.id,
            urls.name,
            urls.created_at,
            latest_checks.status_code as last_status_code,
            latest_checks.created_at as last_check
        FROM urls
        LEFT JOIN LATERAL (
            SELECT status_code, created_at
            FROM url_checks
            WHERE url_checks.url_id = urls.id
            ORDER BY created_at DESC
            LIMIT 1
        ) latest_checks ON true
        ORDER BY urls.created_at DESC
    """
    )

    urls = cur.fetchall()
    cur.close()
    conn.close()
    return urls


def add_check(url_id, check_data):
    """
    Добавляет проверку URL.

    Args:
        url_id: ID URL
        check_data: Словарь c данными проверки
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    created_at = datetime.now(tz=timezone.utc)
    cur.execute(
        """INSERT INTO url_checks
           (url_id, status_code, h1, title, description, created_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            url_id,
            check_data.get("status_code"),
            check_data.get("h1"),
            check_data.get("title"),
            check_data.get("description"),
            created_at,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_checks_by_url_id(url_id):
    """Получает все проверки для URL."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """SELECT * FROM url_checks
           WHERE url_id = %s
           ORDER BY created_at DESC""",
        (url_id,),
    )
    checks = cur.fetchall()
    cur.close()
    conn.close()
    return checks
