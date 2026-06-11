import os
import resend
from django.conf import settings

# Resend API Key লোড করা
resend.api_key = os.environ.get("RESEND_API_KEY")

def send_email(subject, html_content, to_email):
    try:
        params = {
            # অবশ্যই আপনার কেনা ডোমেইনের ইমেইল ব্যবহার করবেন
            "from": "HAT Account <no-reply@hat-bd.com>", 
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        
        # ইমেইল পাঠানো
        response = resend.Emails.send(params)
        return response
        
    except Exception as e:
        # কোনো কারণে ফেইল করলে এরর থ্রো করবে যা আপনার views.py ক্যাচ করবে
        raise Exception(f"Resend Email Error: {str(e)}")
