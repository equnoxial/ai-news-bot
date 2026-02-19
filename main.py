import os
import time
import feedparser
import requests
from typing import Optional, Tuple


# КЛЮЧИ
GROQ_KEY = os.getenv("GROQ_API_KEY")
TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")


def get_ai_content(title: str) -> Tuple[Optional[str], Optional[str]]:
    if not GROQ_KEY:
        print("GROQ_API_KEY не задан. Выход.")
        return None, None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = (
        f"Новость: {title}\n"
        "1. Напиши захватывающий пост для Telegram (заголовок, 3-5 предложений, вопрос). Пиши на русском.\n"
        "2. Через разделитель '|||' напиши 3-6 английских слов для описания картинки (без запятых)."
    )

    try:
        r = requests.post(
            url,
            headers=headers,
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=25,
        )
        if r.status_code != 200:
            print(f"Ошибка Groq: {r.status_code} {r.text[:500]}")
            return None, None

        res = r.json()["choices"][0]["message"]["content"].strip()
        if "|||" not in res:
            print("Ответ Groq без '|||':", res[:300])
            return None, None

        text_part, img_part = res.split("|||", 1)
        return text_part.strip(), img_part.strip()
    except Exception as e:
        print(f"Исключение Groq: {e}")
        return None, None


def generate_image(img_prompt: str) -> Optional[str]:
    """
    Генерация картинки через Replicate (FLUX Schnell).
    """
    if not REPLICATE_TOKEN:
        print("REPLICATE_API_TOKEN не задан. Выход.")
        return None

    api_url = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"
    headers = {
        "Authorization": f"Bearer {REPLICATE_TOKEN}",
        "Content-Type": "application/json",
        "Prefer": "wait=60",
    }

    try:
        resp = requests.post(
            api_url,
            headers=headers,
            json={"input": {"prompt": img_prompt}},
            timeout=70,
        )
        if resp.status_code != 200 and resp.status_code != 201:
            print("Ошибка Replicate:", resp.status_code, resp.text[:500])
            return None

        data = resp.json()
        status = data.get("status")
        output = data.get("output")

        if status != "succeeded":
            print("Replicate не завершил генерацию:", status, str(output)[:200])
            return None

        if not output:
            print("Replicate вернул пустой output.")
            return None

        # output может быть списком URL или строкой
        if isinstance(output, list) and len(output) > 0:
            img_url = output[0] if isinstance(output[0], str) else output[0].get("url")
        elif isinstance(output, str):
            img_url = output
        else:
            print("Неизвестный формат output Replicate:", type(output))
            return None

        if not img_url:
            print("Не удалось получить URL картинки из Replicate.")
            return None

        # Скачиваем картинку
        img_resp = requests.get(img_url, timeout=30)
        if img_resp.status_code != 200:
            print("Ошибка скачивания картинки:", img_resp.status_code)
            return None

        img_path = "p.jpg"
        with open(img_path, "wb") as f:
            f.write(img_resp.content)

        print("Картинка сохранена:", img_path)
        return img_path
    except Exception as e:
        print(f"Ошибка генерации картинки (Replicate): {e}")
        return None


def send_telegram_photo(text: str, img_path: str) -> bool:
    if not TG_TOKEN or not CHAT_ID:
        print("TG_TOKEN или TELEGRAM_CHAT_ID не заданы. Выход.")
        return False

    try:
        with open(img_path, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": text, "parse_mode": "Markdown"},
                files={"photo": photo},
                timeout=20,
            )
        print("Ответ Telegram (sendPhoto):", resp.status_code, resp.text[:200])
        return resp.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False


def main() -> None:
    if not os.path.exists("last_link.txt"):
        with open("last_link.txt", "w", encoding="utf-8") as f:
            f.write("")

    feed_url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    print("Читаю RSS:", feed_url)
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        print("В RSS нет записей.")
        return

    entry = feed.entries[0]
    print("Заголовок новости:", entry.title)
    print("Ссылка новости:", entry.link)

    with open("last_link.txt", "r", encoding="utf-8") as f:
        last = f.read().strip()
    if last == entry.link:
        print("Новость уже была.")
        return

    post_text, img_prompt = get_ai_content(entry.title)
    if not post_text or not img_prompt:
        print("Нет текста или промпта. Ничего не отправляем.")
        return

    print("Промпт для картинки:", img_prompt)
    img_path = generate_image(img_prompt)
    if not img_path or not os.path.exists(img_path):
        print("Картинка не сгенерировалась. Ничего не отправляем и ссылку не сохраняем.")
        return

    ok = send_telegram_photo(post_text, img_path)
    if not ok:
        print("Telegram не принял фото. Ссылку не сохраняем.")
        return

    with open("last_link.txt", "w", encoding="utf-8") as f:
        f.write(entry.link)
    print("Успех: пост опубликован и ссылка сохранена.")


if __name__ == "__main__":
    main()
