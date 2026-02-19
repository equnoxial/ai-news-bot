import os, random, feedparser, requests

# КЛЮЧИ
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HF_TOKEN = os.getenv('HF_TOKEN')

def get_ai_content(title):
    if not GROQ_KEY: return None, None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = f"Новость: {title}\n1. Напиши захватывающий пост для Telegram (заголовок, 3-5 предложений, вопрос). Пиши на русском.\n2. Через разделитель '|||' напиши 3 английских слова для описания картинки."
    
    try:
        r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}, timeout=25)
        if r.status_code == 200:
            res = r.json()['choices'][0]['message']['content'].strip()
            if "|||" in res:
                return res.split("|||")[0].strip(), res.split("|||")[1].strip()
    except: pass
    return None, None

def main():
    # Проверка существования файла, чтобы GitHub не выдавал ошибку 128
    if not os.path.exists("last_link.txt"):
        with open("last_link.txt", "w") as f: f.write("")

    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]

    with open("last_link.txt", "r") as f:
        if f.read().strip() == entry.link:
            print("Новость уже была.")
            return

    post_text, img_prompt = get_ai_content(entry.title)
    if not post_text or not img_prompt: return

    # Генерация через Hugging Face
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": img_prompt}, timeout=40)
        if response.status_code == 200 and len(response.content) > 5000:
            with open('p.jpg', 'wb') as f: f.write(response.content)
            
            with open('p.jpg', 'rb') as photo:
                requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                             data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                             files={"photo": photo})
                
            # Сохраняем ссылку только при успехе
            with open("last_link.txt", "w") as f: f.write(entry.link)
            print("Пост опубликован!")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
