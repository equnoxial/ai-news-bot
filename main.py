import os, random, feedparser, requests, urllib.parse

# Берем ключи
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_ai_text(title):
    # ПРОВЕРКА КЛЮЧА (только для отладки)
    if not GROQ_KEY:
        print("ОШИБКА: GitHub вообще не видит переменную GROQ_API_KEY!")
        return None
    print(f"Ключ найден, начинается на: {GROQ_KEY[:4]}...")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": f"Напиши пост для Телеграм на русском (2 предложения) про это: {title}. Добавь эмодзи."}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        print(f"Groq всё еще выдает ошибку {response.status_code}. Проверь валидность ключа в консоли Groq!")
    except Exception as e:
        print(f"Ошибка сети: {e}")
    return None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]
    
    # Чтобы бот сработал, даже если новость старая (для теста)
    print(f"Обрабатываю новость: {entry.title}")

    ai_text = get_ai_text(entry.title)
    
    if ai_text:
        post_text = ai_text
    else:
        # Если Groq выдал 401, мы попадем сюда
        post_text = f"🤖 *НОВОСТЬ ИИ (БЕЗ ОПИСАНИЯ)*\n\n{entry.title}"

    # Отправка только текста для чистоты эксперимента
    r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", 
                     data={"chat_id": CHAT_ID, "text": post_text, "parse_mode": "Markdown"})
    
    if r.status_code == 200:
        print("Пост отправлен в Telegram!")

if __name__ == "__main__":
    main()
