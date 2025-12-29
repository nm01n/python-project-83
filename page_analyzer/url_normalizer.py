"""Модуль для нормализации и валидации URL."""

from urllib.parse import urlparse

import validators


def normalize_url(url):
    """
    Нормализует URL, оставляя только scheme и netloc.

    Args:
        url: URL для нормализации

    Returns:
        Нормализованный URL
    """
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def validate_url(url):
    """
    Проверяет валидность URL.

    Args:
        url: URL для проверки

    Returns:
        Tuple (is_valid, error_message)
    """
    if not url:
        return False, "URL обязателен"

    if len(url) > 255:
        return False, "URL превышает 255 символов"

    if not validators.url(url):
        return False, "Некорректный URL"

    return True, None
