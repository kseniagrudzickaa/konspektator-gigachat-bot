import os
from dotenv import load_dotenv
import telebot
from gigachat import GigaChat

# Загружаем переменные окружения из .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден. Убедитесь, что он указан в .env")

if not GIGACHAT_CLIENT_SECRET:
    raise RuntimeError("GIGACHAT_CLIENT_SECRET не найден. Убедитесь, что он указан в .env")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

SYSTEM_PROMPT = """
Ты — ИИ-ассистент «Конспектатор».
На основе текста пользователя сформируй:
1) краткий конспект (5–10 пунктов),
2) ключевые тезисы,
3) важные термины с короткими пояснениями,
4) 5–10 вопросов для самопроверки.

Не выдумывай факты, которых нет в исходном тексте.
Пиши структурировано и понятно.
"""

def build_prompt(text: str) -> str:
    return f"{SYSTEM_PROMPT}\n\nТекст пользователя:\n\"\"\"{text}\"\"\""

def ask_gigachat(text: str) -> str:
    """
    Обращение к LLM GigaChat.
    Возвращает сгенерированный текст-ответ.
    """
    with GigaChat(
        credentials=GIGACHAT_CLIENT_SECRET,
        scope=GIGACHAT_SCOPE,
        verify_ssl_certs=False
    ) as giga:
        response = giga.chat(text)
        return response.choices[0].message.content

@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    bot.reply_to(
        message,
        "Привет! Я бот-«Конспектатор».\n\n"
        "Пришли мне текст лекции или статьи — "
        "я сделаю конспект, выделю ключевые тезисы и сформирую вопросы для самопроверки."
    )

@bot.message_handler(content_types=['text'])
def text_handler(message):
    user_text = message.text.strip()

    if len(user_text) < 50:
        bot.reply_to(
            message,
            "Текст слишком короткий. Пришли, пожалуйста, фрагмент лекции или статьи (несколько предложений)."
        )
        return

    try:
        prompt = build_prompt(user_text)
        answer = ask_gigachat(prompt)
        bot.reply_to(message, answer)
    except Exception as e:
        print("Ошибка при работе с GigaChat:", e)
        bot.reply_to(
            message,
            "Произошла ошибка при обращении к ИИ. Попробуй ещё раз позже."
        )

if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling()
