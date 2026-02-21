import os
from time import mktime
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

GROQ_KEY = os.getenv("GROQ_API_KEY")
TG_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122 Safari/537.36"

CAPTION_MAX_LEN = 1024

POSTED_FILE = "posted_links.txt"

RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.technologyreview.com/feed/",
    "https://www.wired.com/feed/tag/ai/latest/rss",
    "https://the-decoder.com/feed/",
]


def load_posted_links():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_posted_link(link):
    with open(POSTED_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")


def get_ai_post(title):
    if not GROQ_KEY:
        print("GROQ_API_KEY не задан. Выход.")
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = (
        f"Новость: {title}\n"
        "Напиши пост для Telegram на русском: заголовок + 4-6 коротких простых предложений + 1 риторический вопрос в конце в отдельном абзаце. "
        "Без ссылок, можно немного эмодзи в начале 1-го предложения, без хэштегов, используй абзацы, выделения ключевых слов для телеграмм канала путем заключения данных слов или слова в две звездочки например: **Важно** или **необходимо**."
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
            return None
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Исключение Groq: {e}")
        return None


def _image_from_feed(entry):
    try:
        if hasattr(entry, "media_content") and entry.media_content:
            url = entry.media_content[0].get("url")
            if url:
                return url
    except Exception:
        pass

    try:
        for link in getattr(entry, "links", []) or []:
            if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image/"):
                return link.get("href")
    except Exception:
        pass

    return None


def get_article_image_url(article_url):
    try:
        r = requests.get(article_url, headers={"User-Agent": UA}, timeout=25)
        if r.status_code != 200:
            print("Не удалось открыть страницу:", r.status_code)
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        def meta(prop=None, name=None):
            if prop:
                tag = soup.find("meta", attrs={"property": prop})
                if tag and tag.get("content"):
                    return tag["content"].strip()
            if name:
                tag = soup.find("meta", attrs={"name": name})
                if tag and tag.get("content"):
                    return tag["content"].strip()
            return None

        return (
            meta(prop="og:image:secure_url")
            or meta(prop="og:image")
            or meta(name="twitter:image")
            or meta(name="twitter:image:src")
        )
    except Exception as e:
        print("Ошибка парсинга страницы:", e)
        return None


def download_image(url):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=40)
        if r.status_code != 200:
            print("Не удалось скачать картинку:", r.status_code)
            return None

        ctype = (r.headers.get("content-type") or "").lower()
        ext = ".jpg"
        if "png" in ctype:
            ext = ".png"
        elif "webp" in ctype:
            ext = ".webp"

        path = "p" + ext
        with open(path, "wb") as f:
            f.write(r.content)

        if len(r.content) < 1000:
            print("Слишком маленький файл, похоже не картинка.")
            return None

        return path
    except Exception as e:
        print("Ошибка скачивания картинки:", e)
        return None


def send_telegram_photo(caption, img_path):
    if not TG_TOKEN or not CHAT_ID:
        print("TG_TOKEN или TELEGRAM_CHAT_ID не заданы.")
        return False

    caption = caption[:CAPTION_MAX_LEN - 3] + "..." if len(caption) > CAPTION_MAX_LEN else caption

    try:
        with open(img_path, "rb") as photo:
            resp = requests.post(
                f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": photo},
                timeout=25,
            )
        ok = resp.status_code == 200 and resp.json().get("ok") is True
        print("Ответ Telegram:", resp.status_code, resp.text[:200])
        return ok
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)
        return False


def fetch_newest_entry(posted_links):
    best_entry = None
    best_time = 0

    for feed_url in RSS_FEEDS:
        print(f"Читаю RSS: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"  Ошибка парсинга фида: {e}")
            continue

        for entry in feed.entries:
            link = getattr(entry, "link", None)
            if not link or link in posted_links:
                continue

            published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            if not published:
                continue

            try:
                t = mktime(published)
            except Exception:
                continue

            if t > best_time:
                best_time = t
                best_entry = entry

    return best_entry


def main():
    if os.path.exists("last_link.txt") and not os.path.exists(POSTED_FILE):
        with open("last_link.txt", "r", encoding="utf-8") as f:
            old_link = f.read().strip()
        if old_link:
            save_posted_link(old_link)
        print("Мигрировал last_link.txt -> posted_links.txt")

    posted_links = load_posted_links()

    entry = fetch_newest_entry(posted_links)
    if not entry:
        print("Нет новых записей ни в одном фиде.")
        return

    title = entry.title
    link = entry.link

    print(f"Самая свежая новость: {title}")
    print(f"Ссылка: {link}")

    image_url = _image_from_feed(entry) or get_article_image_url(link)
    if not image_url:
        print("Не нашёл картинку новости. Ничего не отправляем и ссылку не сохраняем.")
        return

    print("URL картинки:", image_url)
    img_path = download_image(image_url)
    if not img_path:
        print("Картинка не скачалась. Ничего не отправляем и ссылку не сохраняем.")
        return

    post_text = get_ai_post(title)
    if not post_text:
        print("Текст не сгенерировался. Ничего не отправляем и ссылку не сохраняем.")
        return

    if not send_telegram_photo(post_text, img_path):
        print("Telegram не принял фото. Ссылку не сохраняем.")
        return

    save_posted_link(link)
    print("Успех: пост опубликован и ссылка сохранена.")


if __name__ == "__main__":
    main()
