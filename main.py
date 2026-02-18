import os
from google import genai # Оставляем только новый импорт
import feedparser
import requests

# Инициализация
client = genai.Client(api_key=os.getenv('GEMINI_KEY'))

def rewrite_and_image_prompt(title):
    prompt = f"Напиши короткий пост для Telegram на русском про: {title}. В конце добавь IMAGE_PROMPT: [описание картинки на английском]"
    try:
        # Используем только новый метод
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        text = response.text
        if "IMAGE_PROMPT:" in text:
            post, img = text.split("IMAGE_PROMPT:")
            return post.strip(), img.strip()
        return text, "artificial intelligence news"
    except Exception as e:
        print(f"ОШИБКА GEMINI: {e}")
        return title, "tech news"

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    title, link = feed.entries[0].title, feed.entries[0].link

    # Проверка на повторы
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новых новостей нет.")
                return

    post_text, img_prompt = rewrite_and_image_prompt(title)
    
    # Отправка
    token = os.getenv('TG_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080"
    
    r = requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", data={
        "chat_id": chat_id, "photo": img_url, "caption": f"{post_text}\n\n[Источник]({link})", "parse_mode": "Markdown"
    })
    
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(link)
        print("Пост успешно отправлен!")
    else:
        print(f"Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    main()
