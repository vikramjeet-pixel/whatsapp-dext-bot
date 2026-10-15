# 🧾 WhatsApp to Dext & Xero Receipt Bridge

An automated bridge for UK businesses (hotels, restaurants, retail, trades) that allows staff and contractors to snap receipt photos on **WhatsApp**, which are instantly ingested into **Dext Prepare** and reconciled in **Xero**.

---

## ⚡ How It Works

```
[Staff Phone] 
      │ (Snaps receipt & sends note on WhatsApp)
      ▼
[Twilio WhatsApp API]
      │ (Fires HTTP POST Webhook)
      ▼
[FastAPI Bridge] (Hosted on Vercel / Render / Local)
      │ 1. Downloads image securely from Twilio CDN
      │ 2. Formats receipt metadata & tags
      │ 3. Forwards attachment via Resend API
      ▼
[Dext Prepare In-tray] (e.g. company@dext.cc)
      │ (Dext OCR reads supplier, date, total & 20% VAT)
      ▼
[Xero Accounting] (Appears as a matched Draft Bill)
```

---

## 🚀 Quickstart (Local Development)

### 1. Clone & Install
```bash
git clone https://github.com/vikramjeet-pixel/whatsapp-dext-bot.git
cd whatsapp-dext-bot

# Create virtualenv and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

| Variable | Description | Where to find |
| :--- | :--- | :--- |
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID (`AC...`) | [Twilio Console](https://console.twilio.com) |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | [Twilio Console](https://console.twilio.com) |
| `RESEND_API_KEY` | Resend API key (`re_...`) | [Resend Dashboard](https://resend.com/api-keys) |
| `DEXT_INBOUND_EMAIL` | Unique Dext inbound email (`...@dext.cc`) | Dext Prepare → Costs → Add Documents → Email |

### 3. Start the Server
```bash
python main.py
```
Server runs at `http://localhost:8000`.

---

## 🧪 Testing with WhatsApp Sandbox (5 Minutes)

1. In **Twilio Console**, go to **Messaging** → **Try it out** → **Send a WhatsApp message**.
2. Follow instructions to join your sandbox from your mobile (e.g., text `join silver-fox` to `+1 415 523 8886`).
3. Expose your local port 8000 using **ngrok**:
   ```bash
   ngrok http 8000
   ```
4. Copy the forwarding URL (`https://xxxx.ngrok-free.app`).
5. In Twilio Sandbox Settings:
   * Set **"WHEN A MESSAGE COMES IN"** to:
     `https://xxxx.ngrok-free.app/webhook/whatsapp`
   * Method: `HTTP POST`
6. Send a receipt picture from your phone. The bot will reply with a confirmation, and the receipt will appear in Dext within seconds.

---

## 🌐 Deploy to Vercel (Serverless)

This repository is pre-configured for **Vercel** serverless Python execution via `/api/index.py` and `vercel.json`.

1. Push your code to GitHub.
2. In the [Vercel Dashboard](https://vercel.com):
   * Click **Add New** → **Project**.
   * Import this repository.
   * Add the 4 environment variables:
     * `TWILIO_ACCOUNT_SID`
     * `TWILIO_AUTH_TOKEN`
     * `RESEND_API_KEY`
     * `DEXT_INBOUND_EMAIL`
   * Click **Deploy**.
3. Once deployed, set your Twilio Webhook URL to:
   ```
   https://your-vercel-domain.vercel.app/webhook/whatsapp
   ```

---

## ☁️ Alternative Deployments (Render / Railway / Docker)

* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn api.index:app --host 0.0.0.0 --port $PORT`
* **Health Check URL:** `https://your-domain.com/health`

---

## 🛡️ License
MIT License. Built for UK SME automation.
