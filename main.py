import os
import feedparser
import requests

# КЛЮЧИ
GROQ_KEY = os.getenv("GROQ_API_KEY")
TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HF_TOKEN = os.getenv("HF_TOKEN")


def get_ai_content(title: str):
    if not GROQ_KEY:
        print("GROQ_API_KEY не задан. Пост не будет сгенерирован.")
        return None, None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    prompt = (
        f"Новость: {title}\n"
        "1. Напиши захватывающий пост для Telegram (заголовок, 3-5 предложений, вопрос). "
        "Пиши на русском.\n"
        "2. Через разделитель '|||' напиши 3 английских слова для описания картинки."
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
        if "|||" in res:
            text_part, img_part = res.split("|||", 1)
            return text_part.strip(), img_part.strip()
        else:
            print("Ответ Groq без разделителя '|||':", res[:300])
    except Exception as e:
        print(f"Исключение при запросе к Groq: {e}")

    return None, None


def generate_image(img_prompt: str) -> str | None:
    """
    Генерирует картинку через Hugging Face.
    Возвращает путь к файлу или None, если не удалось.
    """
    if not HF_TOKEN:
        print("HF_TOKEN не задан. Картинка сгенерирована не будет.")
        return None

    api_url = (
        "https://api-inference.huggingface.co/models/"
        "stabilityai/stable-diffusion-3.5-large-turbo"
    )
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"inputs": img_prompt},
            timeout=40,
        )
        if response.status_code != 200:
            print(
                "Ошибка Hugging Face:",
                response.status_code,
                response.text[:500],
            )
            return None

        # Проверка на очень маленький ответ (обычно ошибка)
        if len(response.content) < 1000:
            print("Ответ Hugging Face слишком маленький, похоже, не картинка.")
            return None

        img_path = "p.jpg"
        with open(img_path, "wb") as f:
            f.write(response.content)

        print("Картинка успешно сохранена:", img_path)
        return img_path
    except Exception as e:
        print(f"Исключение при запросе к Hugging Face: {e}")
        return None


def send_telegram_photo_or_text(text: str, img_path: str | None):
    """
    Если есть картинка — отправляет фото с подписью.
    Иначе — просто текстовое сообщение.
    """
    if not TG_TOKEN or not CHAT_ID:
        print("TG_TOKEN или TELEGRAM_CHAT_ID не заданы. Нечего отправлять.")
        return

    if img_path and os.path.exists(img_path):
        with open(img_path, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={
                    "chat_id": CHAT_ID,
                    "caption": text,
                    "parse_mode": "Markdown",
                },
                files={"photo": photo},
                timeout=20,
            )
        print("Ответ Telegram (sendPhoto):", resp.status_code, resp.text[:200])
    else:
        resp = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=20,
        )
        print("Ответ Telegram (sendMessage):", resp.status_code, resp.text[:200])


def main():
    # Проверка существования файла, чтобы GitHub не выдавал ошибку 128
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
    if not post_text:
        print("Не удалось сгенерировать текст поста. Выход.")
        return

    # Добавляем ссылку в текст, чтобы она была видна в Telegram
    full_text = f"{post_text}\n\nИсточник: {entry.link}"

    img_path = None
    if img_prompt:
        print("Промпт для картинки:", img_prompt)
        img_path = generate_image(img_prompt)
    else:
        print("Промпт для картинки не получен. Отправлю только текст.")

    send_telegram_photo_or_text(full_text, img_path)

    # Сохраняем ссылку только при успехе отправки
    with open("last_link.txt", "w", encoding="utf-8") as f:
        f.write(entry.link)
    print("Пост обработан и ссылка сохранена.")


if __name__ == "__main__":
    main()
