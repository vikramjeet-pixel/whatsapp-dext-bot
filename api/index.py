import os
import time
from xml.sax.saxutils import escape
from typing import Optional
import requests
from fastapi import FastAPI, Form, Response, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import resend

# Load environment variables if running in local environment
load_dotenv()

app = FastAPI(
    title="WhatsApp to Dext Bridge",
    description="Automated receipt ingestion from WhatsApp directly into Dext Prepare and Xero",
    version="1.0.0"
)

@app.middleware("http")
async def normalize_vercel_paths(request: Request, call_next):
    """Normalize paths forwarded by Vercel serverless rewrites."""
    # Check if Vercel rewrite passed original path in query param
    original_path = request.query_params.get("__path")
    if original_path:
        clean_path = "/" + original_path.lstrip("/")
        request.scope["path"] = clean_path
    else:
        path = request.scope.get("path", "")
        for prefix in ("/api/index.py", "/api/index"):
            if path.startswith(prefix):
                new_path = path[len(prefix):]
                request.scope["path"] = new_path if new_path.startswith("/") else ("/" + new_path)
                break
    return await call_next(request)

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
DEXT_INBOUND_EMAIL = os.getenv("DEXT_INBOUND_EMAIL", "").strip()

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


@app.get("/")
@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint to verify deployment is running."""
    return JSONResponse({
        "status": "healthy",
        "service": "WhatsApp-to-Dext Receipt Bridge",
        "scope_path": request.scope.get("path"),
        "raw_headers": dict(request.headers),
        "configured": {
            "twilio_auth": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
            "resend_api": bool(RESEND_API_KEY),
            "dext_email": bool(DEXT_INBOUND_EMAIL)
        },
        "webhook_url": "/webhook/whatsapp"
    })


@app.post("/webhook/whatsapp")
@app.post("/api/webhook/whatsapp")
async def handle_whatsapp_message(
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None)
):
    """
    Webhook triggered by Twilio when an inbound WhatsApp message or receipt photo is received.
    """
    sender_clean = From.replace("whatsapp:", "").strip()
    caption_text = Body.strip() if Body else ""
    print(f"[*] Inbound message from: {sender_clean} | Media count: {NumMedia} | Caption: '{caption_text}'")

    # If no media attachment was sent, inform the user to take a photo
    if NumMedia == 0 or not MediaUrl0:
        reply_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>⚠️ Please send a photo of the receipt or invoice. Text notes can be added as the photo caption.</Message>
</Response>"""
        return Response(content=reply_twiml, media_type="application/xml")

    # Validate that destination Dext email is configured
    if not DEXT_INBOUND_EMAIL:
        error_twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>❌ Server error: DEXT_INBOUND_EMAIL is not configured. Please check server settings.</Message>
</Response>"""
        return Response(content=error_twiml, media_type="application/xml")

    try:
        # Step 1: Download media file from Twilio's CDN
        auth_creds = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            auth_creds = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        media_resp = None
        if auth_creds:
            try:
                media_resp = requests.get(MediaUrl0, auth=auth_creds, timeout=20)
                media_resp.raise_for_status()
            except requests.exceptions.HTTPError as err:
                if err.response is not None and err.response.status_code == 401:
                    print("[!] 401 with auth credentials, trying unauthenticated fallback...")
                    media_resp = requests.get(MediaUrl0, timeout=20)
                    media_resp.raise_for_status()
                else:
                    raise
        else:
            media_resp = requests.get(MediaUrl0, timeout=20)
            media_resp.raise_for_status()

        image_bytes = media_resp.content

        # Determine file extension from content-type
        content_type = MediaContentType0 or ""
        if "png" in content_type:
            ext = "png"
        elif "pdf" in content_type:
            ext = "pdf"
        elif "heic" in content_type:
            ext = "heic"
        else:
            ext = "jpg"

        timestamp = int(time.time())
        filename = f"receipt_{sender_clean.replace('+', '')}_{timestamp}.{ext}"

        # Step 2: Compose and dispatch email with receipt attachment to Dext
        notes_display = caption_text if caption_text else "No caption provided"
        subject = f"Receipt from {sender_clean}: {notes_display[:40]}"

        email_payload = {
            "from": "Receipts Bot <onboarding@resend.dev>",
            "to": [DEXT_INBOUND_EMAIL],
            "subject": subject,
            "html": f"""
            <div style="font-family: sans-serif; line-height: 1.5;">
                <h3 style="color: #1a1a1a;">New Receipt via WhatsApp</h3>
                <p><strong>Sender:</strong> {escape(sender_clean)}</p>
                <p><strong>Notes / Job:</strong> {escape(notes_display)}</p>
                <p><strong>Received At:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))}</p>
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 15px 0;">
                <small style="color: #777;">Automated ingestion by WhatsApp Dext Bridge</small>
            </div>
            """,
            "attachments": [
                {
                    "filename": filename,
                    "content": list(image_bytes)
                }
            ]
        }

        email_result = resend.Emails.send(email_payload)
        print(f"[+] Receipt sent to Dext ({DEXT_INBOUND_EMAIL}). Resend ID: {email_result}")

        reply_message = f"✅ Receipt received! Processed to Dext for accounting.\nNotes: \"{notes_display}\""

    except Exception as exc:
        print(f"[-] Error processing receipt from {sender_clean}: {exc}")
        reply_message = f"❌ Error processing receipt: {str(exc)[:120]}. Please try again."

    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escape(reply_message)}</Message>
</Response>"""
    return Response(content=twiml_response, media_type="application/xml")
