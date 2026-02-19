import os, random, feedparser, requests, io

# КЛЮЧИ
GROQ_KEY = os.getenv('GROQ_API_KEY')
TG_TOKEN = os.getenv('TG_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HF_TOKEN = os.getenv('HF_TOKEN') # Новый секрет для стабильных картинок

def get_ai_content(title):
    if not GROQ_KEY: return None, None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    prompt = f"""Напиши крутой пост для Telegram канала про новость: {title}.
    Сделай заголовок с эмодзи, разбор сути с интересом простыми словами (4-6 предложений).
    Пиши на русском. Используй Markdown, отступы для каждого абзаца, выделения для некоторых ключевых словосочетаний или предложений."""
    
    try:
        r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]}, timeout=25)
        if r.status_code == 200:
            res = r.json()['choices'][0]['message']['content'].strip()
            if "|||" in res:
                return res.split("|||")[0].strip(), res.split("|||")[1].strip()
    except: pass
    return None, None

def main():
    feed = feedparser.parse("https://techcrunch.com/category/artificial-intelligence/feed/")
    if not feed.entries: return
    entry = feed.entries[0]

    if os.path.exists("last_link.txt"):
        with open("last_link.txt", "r") as f:
            if f.read().strip() == entry.link: return

    post_text, img_prompt = get_ai_content(entry.title)
    if not post_text or not img_prompt: return

    # НОВЫЙ ГЕНЕРАТОР: Hugging Face (намного стабильнее Pollinations)
    print(f"--- Генерация картинки через Hugging Face: {img_prompt} ---")
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": img_prompt}, timeout=40)
        
        if response.status_code == 200 and len(response.content) > 10000:
            with open('p.jpg', 'wb') as f:
                f.write(response.content)
            
            with open('p.jpg', 'rb') as photo:
                r_tg = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                                    data={"chat_id": CHAT_ID, "caption": post_text, "parse_mode": "Markdown"},
                                    files={"photo": photo})
                
                if r_tg.status_code == 200:
                    print("--- УСПЕХ: Пост отправлен! ---")
                    with open("last_link.txt", "w") as f: f.write(entry.link)
                    return
        else:
            print(f"--- Ошибка генератора: {response.status_code}. Проверьте HF_TOKEN. ---")
    except Exception as e:
        print(f"--- Сбой: {e} ---")

if __name__ == "__main__":
    main()
