import resend
import os

resend.api_key = os.environ.get("RESEND_API_KEY")


def send_email(subject, html_content, to_email):
    try:
        resend.Emails.send({
            "from": "HAT <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": html_content,
        })
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise e