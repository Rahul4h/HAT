from django.core.mail import EmailMessage
from django.conf import settings

def send_email(subject, html_content, to_email):
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)