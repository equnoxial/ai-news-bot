import os
import random
import feedparser
import requests
import time
from google import genai

# Настройки
GEMINI_KEY = os.getenv('GEMINI_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

client = genai.Client(api_key=GEMINI_KEY)

def get_ai_content(title):
    model_name = "gemini-2.0-flash" 
    prompt = f"Напиши короткий пост для Telegram на русском про: {title}. В конце добавь IMAGE_PROMPT: [описание картинки на английском]"
    
    try:
        print(f"Пробую свежий ключ с моделью: {model_name}...")
        response = client.models.generate_content(model=model_name, contents=prompt)
        
        if response.text:
            print("Ура! ИИ ответил.")
            full_text = response.text
            if "IMAGE_PROMPT:" in full_text:
                text, img_p = full_text.split("IMAGE_PROMPT:")
                return text.strip(), img_p.strip()
            return full_text, "futuristic technology"
            
    except Exception as e:
        print(f"Даже с новым ключом ошибка: {e}")
        return title, "artificial intelligence"
            
        except Exception as e:
            # Если ошибка, пишем её и идем к следующей модели
            print(f"Не вышло с {model_name}: {e}")
            time.sleep(1) # Небольшая пауза перед следующей попыткой
            continue

    # Если вообще ни одна не сработала
    print("ВСЕ МОДЕЛИ ОТКАЗАЛИ.")
    return title, "artificial intelligence"

def main():
    # 1. Получаем новость
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    title, link = feed.entries[0].title, feed.entries[0].link

    # 2. Проверяем, была ли она уже
    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == link:
                print("Новых новостей нет.")
                return

    print(f"Обрабатываю: {title}")
    
    # 3. Генерируем текст (перебор моделей внутри)
    post_text, img_prompt = get_ai_content(title)
    
    # 4. Генерируем картинку
    seed = random.randint(1, 100000)
    # Используем Flux (лучшее качество)
    img_url = f"https://pollinations.ai/p/{img_prompt.replace(' ', '%20')}?width=1080&height=1080&seed={seed}&model=flux"
    
    # 5. Отправляем в Telegram
    tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": img_url,
        "caption": f"{post_text}\n\n[Источник]({link})",
        "parse_mode": "Markdown"
    }
    
    r = requests.post(tg_url, data=payload)
    if r.status_code == 200:
        with open("last_link.txt", "w") as f: f.write(link)
        print("Пост успешно отправлен!")
    else:
        print(f"Ошибка Telegram: {r.text}")

if __name__ == "__main__":
    main()
