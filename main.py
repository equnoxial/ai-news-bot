import os
import random
import feedparser
import requests
import urllib.parse

# Получаем секреты
HF_TOKEN = os.getenv('HF_TOKEN')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    """Генерирует короткий текст через Mistral AI с таймаутом."""
    print(f"Запрос к ИИ для: {title}")
    api_url = "https://api-inference.huggingface.co/models/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"<s>[INST] Напиши очень короткий и интересный пост для Телеграм на русском языке на основе этого заголовка: {title}. Используй 1-2 эмодзи. [/INST]"
    
    try:
        # Ждем ответ не больше 15 секунд
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=15)
        if response.status_code == 200:
            result = response.json()
            # Очищаем ответ от служебных тегов
            text = result[0]['generated_text'].split("[/INST]")[-1].strip()
            if text: return text
    except Exception as e:
        print(f"ИИ не ответил или ошибка: {e}")
    
    # Если ИИ не справился, отдаем просто заголовок
    return f"🤖 *НОВОСТЬ ИИ*\n\n{title}"

def main():
    # Читаем ленту новостей
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Проверяем, не постили ли мы это уже
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link:
                print("Свежих новостей нет.")
                return

    # Готовим контент
    post_text = get_ai_text(entry.title)
    
    # ФИКС КАРТИНКИ: Берем только первые 4 слова для генерации, чтобы ссылка была простой
    short_title = " ".join(entry.title.split()[:4])
    encoded_prompt = urllib.parse.quote(f"cyberpunk aesthetic {short_title}")
    # Добавляем случайное число (seed), чтобы картинка всегда была разной
    img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1080&nologo=true&seed={random.randint(1,9999)}"
    
    caption = post_text
    
    print(f"Пробую отправить фото: {img_url}")

    # Попытка 1: Отправляем как фото
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", 
                         data={"chat_id": CHAT_ID, "photo": img_url, "caption": caption, "parse_mode": "Markdown"})
        
        if r.status_code == 200:
            print("УСПЕХ! Фото и текст отправлены.")
            # Сохраняем ссылку только при успехе
            with open("last_link.txt", "w") as f: f.write(entry.link)
            return # Выходим, всё отлично
        else:
             print(f"Ошибка отправки фото (Код {r.status_code}): {r.text}")
    except Exception as e:
        print(f"Критическая ошибка запроса: {e}")

    # Попытка 2 (Страховка): Если фото не прошло, отправляем текст с ссылкой на картинку
    print("Пробую отправить запасной вариант (только текст)...")
    caption_with_link = f"{post_text}\n\n[Картинка к новости]({img_url})"
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                  data={"chat_id": CHAT_ID, "text": caption_with_link, "parse_mode": "Markdown"})
    # Тоже считаем успехом и сохраняем ссылку
    with open("last_link.txt", "w") as f: f.write(entry.link)

if __name__ == "__main__":
    main()
