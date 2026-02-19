import os
import feedparser
import requests
from typing import Optional, Tuple

from huggingface_hub import InferenceClient


# КЛЮЧИ
GROQ_KEY = os.getenv("GROQ_API_KEY")
TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HF_TOKEN = os.getenv("HF_TOKEN")


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
    if not HF_TOKEN:
        print("HF_TOKEN не задан. Выход.")
        return None

    try:
        # без provider="auto" — провайдера задаём в самом вызове
        client = InferenceClient(api_key=HF_TOKEN)

        image = client.text_to_image(
            img_prompt,
            model="stabilityai/stable-diffusion-3.5-large-turbo",
            provider="hf-inference",  # один из доступных: fal-ai, hf-inference, replicate, sambanova, together
        )

        img_path = "p.jpg"
        image.save(img_path, format="JPEG", quality=95)
        print("Картинка сохранена:", img_path)
        return img_path
    except Exception as e:
        print(f"Ошибка генерации картинки (HF InferenceClient): {e}")
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
