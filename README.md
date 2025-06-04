# 💬 Chatbot template

A simple Streamlit app that shows how to build a chatbot using OpenAI's GPT-3.5.

### WatkiBot

The app has been extended to serve as **WatkiBot**, a legal assistant that
maintains separate conversations for each case. Choose a client from the
sidebar to focus the chat on that case. Each case preserves its own chat
history and OpenAI thread so you can switch back and forth without losing
context.

The app expects an `OPENAI_API_KEY` and optionally an `ASSISTANT_ID` in
your Streamlit secrets. If no API key is found, you'll be prompted for one
when you start the app.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://chatbot-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
