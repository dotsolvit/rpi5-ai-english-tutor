#RPi5EnglishTutor bot.py v2
#13.09.2026

import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from openai import AsyncOpenAI

# ==============================================================================
# ІНІЦІАЛІЗАЦІЯ ТА КОНФІГУРАЦІЯ / INITIALIZATION & CONFIGURATION
# ==============================================================================

# Завантажуємо конфігурацію та фінансові коефіцієнти з прихованого файлу .env
# Load configuration and financial coefficients from the hidden .env file
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Считуємо тарифи, винесені в оточення (За замовчуванням стоять актуальні ціни)
# Read rates moved to the environment (Defaults are set to current market prices)
# Официальные тарифы OpenAI / Official OpenAI Pricing: https://developers.openai.com/api/docs/pricing
PRICE_WHISPER_PER_MIN = float(os.getenv("PRICE_WHISPER_PER_MIN", 0.006))
PRICE_GPT_INPUT_PER_1M = float(os.getenv("PRICE_GPT_INPUT_PER_1M", 0.15))
PRICE_GPT_OUTPUT_PER_1M = float(os.getenv("PRICE_GPT_OUTPUT_PER_1M", 0.60))
PRICE_TTS_PER_1M = float(os.getenv("PRICE_TTS_PER_1M", 15.00))

# Ініціалізація клієнтів систем розробки
# Initializing development system clients
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
openai_client = AsyncOpenAI(api_key=OPENAI_KEY)

LOG_FILE = "billing_log.txt"

# Педагогічна інструкція для ШІ-асистента
# Pedagogical instruction for the AI assistant
SYSTEM_PROMPT = (
    "You are an AI English Tutor. Your goal is to help the user practice spoken English "
    "in a friendly, supportive, and engaging way. Follow these strict rules:\n"
    "1. Role: Act as a patient, certified native English teacher.\n"
    "2. Communication style: Keep your spoken responses short, clear, and natural (2-4 sentences max).\n"
    "3. Correction Rule: ALWAYS start your text response with corrections format: '*Correction: [text]*' followed by a line break.\n"
    "4. Flow: End your message with an open-ended question to keep the conversation going.\n"
    "5. Tone: Be encouraging. Never make the user feel bad about mistakes."
)

chat_histories = {}

# ==============================================================================
# ДОПОМІЖНІ ТА ФІНАНСОВІ ФУНКЦІЇ / UTILITY & FINANCIAL FUNCTIONS
# ==============================================================================

async def convert_ogg_to_mp3_async(input_path: str, output_path: str) -> float:
    """
    Асинхронно викликає системний ffmpeg для конвертації звуку та обчислення тривалості.
    Взагалі не використовує бібліотеки pydub чи застарілий audioop.
    Asynchronously invokes system ffmpeg to convert sound and compute duration.
    Does not use pydub or deprecated audioop libraries at all.
    """
    # Команда конвертації через системний ffmpeg
    # Conversion command via system ffmpeg
    cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
    
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Використовуємо ffprobe для точного виміру тривалості аудіофайлу
    # Use ffprobe to precisely measure the audio file duration
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", output_path]
    probe_process = await asyncio.create_subprocess_exec(
        *probe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await probe_process.communicate()
    
    try:
        return float(stdout.decode().strip())
    except ValueError:
        return 0.0


def get_last_financial_totals() -> tuple[float, float]:
    """
    Зчитує останній рядок логу для миттєвого отримання наростаючого підсумку.
    Reads the last line of the log for instant retrieval of the running total.
    """
    if not os.path.exists(LOG_FILE):
        return 0.0, 0.0
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines and lines[-1].strip():
                parts = lines[-1].strip().split(",")
                if len(parts) == 2:
                    return float(parts[0]), float(parts[1])
    except Exception as e:
        print(f"Billing read error: {e}")
    return 0.0, 0.0


def log_and_calculate_cost(whisper_sec: float, gpt_input: int, gpt_output: int, tts_chars: int) -> tuple[float, float]:
    """
    Обчислює вартість кроку та записує її разом із сумарним наростаючим підсумком.
    Calculates step cost and logs it together with the running total.
    """
    whisper_cost = (whisper_sec / 60.0) * PRICE_WHISPER_PER_MIN
    gpt_in_cost = (gpt_input / 1_000_000.0) * PRICE_GPT_INPUT_PER_1M
    gpt_out_cost = (gpt_output / 1_000_000.0) * PRICE_GPT_OUTPUT_PER_1M
    tts_cost = (tts_chars / 1_000_000.0) * PRICE_TTS_PER_1M
    
    step_cost = whisper_cost + gpt_in_cost + gpt_out_cost + tts_cost
    _, previous_total = get_last_financial_totals()
    new_total_spent = previous_total + step_cost
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{step_cost:.5f},{new_total_spent:.5f}\n")
        
    return step_cost, new_total_spent

# ==============================================================================
# ОБРОБНИКИ ПОВІДОМЛЕНЬ / MESSAGE HANDLERS
# ==============================================================================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    chat_id = message.chat.id
    chat_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    _, total_spent = get_last_financial_totals()
    
    welcome_text = (
        f"👋 Hello! I am your personal English tutor. Let's practice!\n"
        f"🇺🇦 Привіт! Я твій особистий репетитор англійської. Почнімо тренування!\n\n"
        f"`⚙️ Total budget spent: ${total_spent:.4f}`"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message(F.voice)
async def handle_voice_message(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
        
    status_message = await message.answer("📥 Processing... / Обробляю...")

    ogg_path = f"voice_{chat_id}.ogg"
    mp3_path = f"voice_{chat_id}.mp3"
    reply_mp3_path = f"reply_{chat_id}.mp3"

    try:
        # 1. ЗАВАНТАЖЕННЯ / DOWNLOAD
        file_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(file_info.file_path, ogg_path)

        # 2. АСИНХРОННА КОНВЕРТАЦІЯ ТА ВИМІР ЧАСУ / ASYNC CONVERSION & DURATION MEASUREMENT
        audio_duration_seconds = await convert_ogg_to_mp3_async(ogg_path, mp3_path)

        # 3. WHISPER STT (Розпізнавання тексту) / WHISPER STT (Text recognition)
        with open(mp3_path, "rb") as audio_file:
            transcript = await openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language="en"
            )
        
        user_text = transcript.text
        chat_histories[chat_id].append({"role": "user", "content": user_text})

        # 4. GPT-4O-MINI ВІДПОВІДЬ / GPT-4O-MINI RESPONSE
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini", messages=chat_histories[chat_id]
        )
        
        ai_response_text = response.choices[0].message.content
        chat_histories[chat_id].append({"role": "assistant", "content": ai_response_text})

        gpt_in_tokens = response.usage.prompt_tokens
        gpt_out_tokens = response.usage.completion_tokens

        # 5. OPENAI TTS (Генерація мовлення) / OPENAI TTS (Speech generation)
        tts_response = await openai_client.audio.speech.create(
            model="tts-1", voice="alloy", input=ai_response_text
        )
        
        # Сучасний бінарний запис контенту без виклику застарілих stream методів
        # Modern binary content writing without invoking deprecated stream methods
        with open(reply_mp3_path, "wb") as f:
            f.write(tts_response.content)
            
        tts_characters = len(ai_response_text)

        # 6. БІЛІНГ / BILLING
        step_cost, total_spent = log_and_calculate_cost(
            whisper_sec=audio_duration_seconds,
            gpt_input=gpt_in_tokens,
            gpt_output=gpt_out_tokens,
            tts_chars=tts_characters
        )

        # 7. ВІДПРАВКА СФОРМОВАНОЇ ВІДПОВІДІ / DISPATCHING THE FORMULATED RESPONSE
        await status_message.delete()

        # Красиве оформлення: відображаємо, що сказав користувач, та додаємо дрібний фінансовий рядок
        # Beautiful styling: displaying what the user said and adding a small financial line
        full_reply_text = (
            f"👤 *You said:* _{user_text}_\n\n"
            f"{ai_response_text}\n\n"
            f"`Cost: ${step_cost:.4f} | Sum: ${total_spent:.4f}`"
        )

        await message.answer(full_reply_text, parse_mode="Markdown")
        
        voice_file = types.FSInputFile(reply_mp3_path)
        await message.answer_voice(voice_file)

    except Exception as e:
        print(f"Error: {e}")
        await status_message.edit_text("❌ Error occurred / Сталася помилка.")
    
    finally:
        # Видалення залишків тимчасових медіафайлів
        # Cleaning up remaining temporary media files
        for path in [ogg_path, mp3_path, reply_mp3_path]:
            if os.path.exists(path):
                os.remove(path)

async def main():
    print("=========================================")
    print("Bot 2.0 started successfully on RPi5 (Pure Asynchronous Pipe)!")
    print("=========================================")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
