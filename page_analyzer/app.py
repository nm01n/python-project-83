"""Главный модуль Flask приложения."""

import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from page_analyzer import database, parser, url_normalizer

# Загружаем .env только если файл существует (для локальной разработки)
if os.path.exists(".env"):
    load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Проверка что SECRET_KEY установлен
if not app.config["SECRET_KEY"]:
    raise ValueError("SECRET_KEY не установлен! Установите переменную окружения SECRET_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен! Установите переменную окружения DATABASE_URL")


@app.route("/")
def index():
    """Отображает главную страницу."""
    return render_template("index.html")


@app.route("/urls", methods=["POST"])
def add_url():
    """Добавляет новый URL в базу данных."""
    url = request.form.get("url")

    # Валидация URL
    is_valid, error_message = url_normalizer.validate_url(url)
    if not is_valid:
        flash(error_message, "danger")
        return render_template("index.html"), 422

    # Нормализация URL
    normalized_url = url_normalizer.normalize_url(url)

    # Проверяем существование URL
    existing_url = database.get_url_by_name(normalized_url)
    if existing_url:
        flash("Страница уже существует", "info")
        return redirect(url_for("show_url", id=existing_url["id"]))

    # Добавляем новый URL
    url_id = database.add_url(normalized_url)

    flash("Страница успешно добавлена", "success")
    return redirect(url_for("show_url", id=url_id))


@app.route("/urls")
def urls():
    """Отображает список всех URLs."""
    urls_list = database.get_all_urls()
    return render_template("urls.html", urls=urls_list)


@app.route("/urls/<int:id>")
def show_url(id):
    """Отображает страницу конкретного URL."""
    url = database.get_url_by_id(id)

    if url is None:
        flash("URL не найден", "danger")
        return redirect(url_for("index"))

    checks = database.get_checks_by_url_id(id)

    return render_template("url.html", url=url, checks=checks)


@app.route("/urls/<int:id>/checks", methods=["POST"])
def add_check(id):
    """Запускает проверку URL."""
    url = database.get_url_by_id(id)

    if url is None:
        flash("URL не найден", "danger")
        return redirect(url_for("index"))

    # Выполняем проверку сайта
    check_data = parser.check_url(url["name"])

    if check_data is None:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("show_url", id=id))

    # Сохраняем результаты проверки
    database.add_check(id, check_data)

    flash("Страница успешно проверена", "success")
    return redirect(url_for("show_url", id=id))
