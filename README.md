---
title: SEO Agent
emoji: ✍️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# SEO Agent (Chainlit + OpenAI)

This is a live SEO Agent built using the [OpenAI SDK](https://github.com) and [Chainlit](https://docs.chainlit.io). It uses [Oxylabs AI Studio](https://oxylabs.io) for data retrieval and SEO analysis.

## 🚀 Deployment on Railway

1. **Connect GitHub**: Import this repo into [Railway.app](https://railway.app).
2. **Environment Variables**: Add the following in the **Variables** tab:
   - `OPENAI_API_KEY`: Your OpenAI key.
   - `CHAINLIT_AUTH_SECRET`: Generate one or use a random string.
3. **Start Command**: Set this in **Settings > Deploy**:
   `chainlit run main.py --host 0.0.0.0 --port $PORT`

## 🛠️ Local Setup

1. Install dependencies:
   ```bash
   pip install .
