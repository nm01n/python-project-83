"""Модуль для парсинга HTML и извлечения SEO-данных."""

import requests
from bs4 import BeautifulSoup


def check_url(url):
    """
    Выполняет HTTP-запрос к URL и извлекает информацию.

    Args:
        url: URL для проверки

    Returns:
        Словарь с данными или None при ошибке
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        return parse_html(response.text, response.status_code)
    except requests.exceptions.RequestException:
        return None


def parse_html(html, status_code):
    """
    Парсит HTML и извлекает SEO-данные.

    Args:
        html: HTML контент страницы
        status_code: HTTP статус-код

    Returns:
        Словарь с извлеченными данными
    """
    soup = BeautifulSoup(html, "html.parser")

    return {
        "status_code": status_code,
        "h1": extract_h1(soup),
        "title": extract_title(soup),
        "description": extract_description(soup),
    }


def extract_h1(soup):
    """Извлекает текст из тега h1."""
    h1_tag = soup.find("h1")
    if h1_tag:
        text = h1_tag.get_text().strip()
        return text[:255] if text else None
    return None


def extract_title(soup):
    """Извлекает текст из тега title."""
    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text().strip()
        return text[:255] if text else None
    return None


def extract_description(soup):
    """Извлекает content из meta-тега description."""
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag and description_tag.get("content"):
        return description_tag.get("content").strip()
    return None
