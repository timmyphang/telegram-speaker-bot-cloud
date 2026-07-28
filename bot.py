#!/usr/bin/env python3
# Cloud Telegram Bot - OpenRouter (Ling 3.0 Flash) + Brave Search + Google Home Broadcast
# Runs on GCP VM, broadcasts TTS to Google Home via Google Assistant SDK

import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import json
import io
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
try:
    from google_broadcast import broadcast_to_google_home
except ImportError:
    def broadcast_to_google_home(msg):
        print("Broadcast skipped (Google Assistant not available): " + str(msg))
        return False

load_dotenv()

# Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# OpenRouter Configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Brave Search API
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")


def brave_search(query):
    """Search the web using Brave Search API"""
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": BRAVE_API_KEY,
        "Accept": "application/json"
    }
    params = {
        "q": query,
        "count": 5
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        results = response.json()
        search_results = []
        if "web" in results and "results" in results["web"]:
            for item in results["web"]["results"][:5]:
                title = item.get("title", "")
                description = item.get("description", "")
                if title:
                    search_results.append(f"{title}: {description}")
        return search_results
    except Exception as e:
        print(f"Brave search error: {e}")
        return []


def call_llm(user_message, search_context="", image_url=None):
    """Call DeepSeek API"""
    if image_url:
        system_prompt = "When analyzing images: If there is text or words in the image, transcribe ONLY the text exactly as it appears. Do NOT add descriptions, explanations, or any additional content beyond the transcribed text. Only respond with the text found in the image."
    else:
        system_prompt = "You are a helpful assistant. Answer the user question using the provided search results. Keep your response under 50 words so it can be spoken aloud. Use metric measurements (km, kg, Celsius). If no search results are provided, use your own knowledge."

    messages = [{"role": "system", "content": system_prompt}]

    if image_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        })
    else:
        if search_context:
            user_msg = f"Search results:\n{search_context}\n\nUser question: {user_message}"
        else:
            user_msg = user_message
        messages.append({"role": "user", "content": user_msg})

    try:
        url = f"{DEEPSEEK_BASE_URL}/chat/completions"
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "max_tokens": 200,
            "thinking": {"type": "disabled"},
            "temperature": 0.7
        }
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return None
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Send me a message or image and I'll respond and speak it on Google Home."
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image messages - download and analyze"""
    await update.message.chat.send_action("typing")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_buffer = io.BytesIO()
        await file.download_to_memory(out=image_buffer)
        image_buffer.seek(0)
        import base64
        image_base64 = base64.b64encode(image_buffer.read()).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{image_base64}"

        llm_response = call_llm(
            "Transcribe all text visible in this image exactly as it appears.",
            image_url=image_data_url
        )
        if llm_response:
            broadcast_to_google_home(llm_response)
            await update.message.reply_text(llm_response)
        else:
            await update.message.reply_text("Sorry, I couldn't analyze the image.")
    except Exception as e:
        print(f"Image error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action("typing")
    try:
        search_results = brave_search(user_message)
        search_context = ""
        if search_results:
            search_context = "\n\n".join(search_results[:3])

        await update.message.chat.send_action("typing")
        llm_response = call_llm(user_message, search_context)
        if llm_response:
            broadcast_to_google_home(llm_response)
            await update.message.reply_text(llm_response)
        else:
            await update.message.reply_text("Sorry, I didn't get a response from the LLM.")
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text(f"Error: {str(e)}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Cloud Telegram bot running with DeepSeek V4 Flash + Brave Search + Google Home Broadcast...")
    app.run_polling(poll_interval=1)


if __name__ == "__main__":
    main()
