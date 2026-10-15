import os
import uvicorn
from api.index import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting WhatsApp Dext Bridge on http://localhost:{port}")
    print(f"👉 Local Webhook URL: http://localhost:{port}/webhook/whatsapp")
    uvicorn.run("api.index:app", host="0.0.0.0", port=port, reload=True)
