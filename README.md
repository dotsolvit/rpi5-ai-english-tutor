# Raspberry Pi 5 AI English Spoken Tutor 🤖🗣️

🌐 [Читати мене Українською](README_uk.md) | **Read me in English**

An asynchronous, lightweight Telegram bot running on **Raspberry Pi 5** that acts as a personal spoken English tutor. Powered by OpenAI Whisper & GPT-4o-mini with a native async `ffmpeg` audio pipeline and a precise cumulative token billing tracker.

---

## 🗺️ System Architecture

Below is the visual lifecycle of a single voice turn inside the system:

![System Architecture](assets/architecture.png)

1. **User** records and sends a voice message via Telegram on an Android smartphone.
2. **Raspberry Pi 5** downloads the `.ogg` file and asynchronously converts it to `.mp3` using `ffmpeg` tools.
3. Audio is transmitted to **OpenAI Cloud**:
   * **Whisper** transcribes speech to text.
   * **GPT-4o-mini** processes context, evaluates grammar mistakes, and forms a pedagogical response.
   * **OpenAI TTS** turns the response text back into a high-quality voice file.
4. Token expenditure and cost calculations are instantly logged into `billing_log.txt` with running totals.
5. **Raspberry Pi 5** replies to the user with a text breakdown of errors and a native voice message.

---

## 🛠️ Prerequisites & Hardware

* **Hardware:** Raspberry Pi 5 (any RAM variant) with an active cooling system.
* **OS:** Pure Raspberry Pi OS (Debian 12/13 based).
* **Software dependency:** `ffmpeg` installed globally.
* **API:** OpenAI Developer account with a prepaid balance.

---

## 🚀 Installation & Setup

1. **Clone the repository and enter the directory:**
   ```bash
   git clone https://github.com
   cd rpi5-ai-english-tutor
   ```

2. **Install system-wide dependencies:**
   ```bash
   sudo apt update && sudo apt install ffmpeg -y
   ```

3. **Set up a Python virtual environment & install packages:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file based on the provided sample:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Fill in your individual API tokens and save the file.

5. **Run the tutor system:**
   ```bash
   python src/bot.py
   ```

---

## 📊 Cost Tracking & Transparency

The bot automatically keeps a clear record of expenditures at the bottom of each chat reply:
`Cost: $0.0022 | Sum: $0.0058`

All billing events are tracked dynamically without heavy database engines, relying on quick filesystem reads from `b
