import requests
from django.conf import settings

def send_telegram_message(chat_id: str, message: str) -> bool:
    """
    Envía un mensaje de texto a un usuario en Telegram.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    return response.status_code == 200


def send_telegram_document(chat_id: str, file_obj, filename: str) -> bool:
    """
    Envía un archivo (PDF, Excel, etc.) a un usuario en Telegram.
    file_obj debe ser un objeto tipo BytesIO o archivo abierto en modo binario.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    files = {
        "document": (filename, file_obj)
    }
    data = {
        "chat_id": chat_id
    }
    response = requests.post(url, data=data, files=files)
    return response.status_code == 200