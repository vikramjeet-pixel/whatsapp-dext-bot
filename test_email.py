import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
target_email = "vikramjeet.-3@mail.bcu.ac.uk"

# Minimal valid 1x1 transparent PNG
dummy_png = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

print(f"[*] Testing Resend delivery to: {target_email}")
try:
    resp = resend.Emails.send({
        "from": "Receipts Bot <onboarding@resend.dev>",
        "to": [target_email],
        "subject": "Test Receipt: Screwfix Tools £32.50",
        "html": "<p><strong>Sender:</strong> +447000000000</p><p><strong>Notes:</strong> Screwfix Tools £32.50</p>",
        "attachments": [
            {
                "filename": "screwfix_receipt.png",
                "content": list(dummy_png)
            }
        ]
    })
    print(f"[+] Success! Email dispatched with attachment. ID: {resp}")
except Exception as e:
    print(f"[-] Failed to dispatch email: {e}")
