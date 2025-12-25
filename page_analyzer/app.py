import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import validators

# Загружаем .env только если файл существует (для локальной разработки)
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Проверка что SECRET_KEY установлен
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY не установлен! Установите переменную окружения SECRET_KEY")

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не установлен! Установите переменную окружения DATABASE_URL")


def get_db_connection():
    """Создает подключение к базе данных"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/urls', methods=['POST'])
def add_url():
    url = request.form.get('url')
    
    # Валидация URL
    if not url:
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 422
    
    if len(url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return render_template('index.html'), 422
    
    if not validators.url(url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422
    
    # Нормализация URL (оставляем только scheme и netloc)
    parsed_url = urlparse(url)
    normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Проверяем, существует ли URL
    cur.execute('SELECT id FROM urls WHERE name = %s', (normalized_url,))
    existing_url = cur.fetchone()
    
    if existing_url:
        flash('Страница уже существует', 'info')
        cur.close()
        conn.close()
        return redirect(url_for('show_url', id=existing_url['id']))
    
    # Добавляем новый URL
    created_at = datetime.now()
    cur.execute(
        'INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id',
        (normalized_url, created_at)
    )
    url_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('show_url', id=url_id))


@app.route('/urls')
def urls():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Получаем все URLs с датой последней проверки
    cur.execute('''
        SELECT 
            urls.id,
            urls.name,
            urls.created_at,
            MAX(url_checks.created_at) as last_check
        FROM urls
        LEFT JOIN url_checks ON urls.id = url_checks.url_id
        GROUP BY urls.id, urls.name, urls.created_at
        ORDER BY urls.created_at DESC
    ''')
    urls_list = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('urls.html', urls=urls_list)


@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Получаем информацию о URL
    cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
    url = cur.fetchone()
    
    if url is None:
        cur.close()
        conn.close()
        flash('URL не найден', 'danger')
        return redirect(url_for('index'))
    
    # Получаем все проверки для этого URL
    cur.execute(
        'SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC',
        (id,)
    )
    checks = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('url.html', url=url, checks=checks)


@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_check(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Проверяем существование URL
    cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
    url = cur.fetchone()
    
    if url is None:
        cur.close()
        conn.close()
        flash('URL не найден', 'danger')
        return redirect(url_for('index'))
    
    # Создаем новую проверку (пока только с базовыми полями)
    created_at = datetime.now()
    cur.execute(
        '''INSERT INTO url_checks 
           (url_id, created_at) 
           VALUES (%s, %s)''',
        (id, created_at)
    )
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Страница успешно проверена', 'success')
    return redirect(url_for('show_url', id=id))
