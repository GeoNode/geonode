import os
from django.core.management.base import BaseCommand
from geonode.utils import send_email  # Replace with the actual path to your email utility

class Command(BaseCommand):
    help = 'Test email sending with Microsoft Graph API'

    def handle(self, *args, **kwargs):
        # Replace with your test recipient email
        recipient_email = "recipient@example.com"
        subject = "Test Email"
        body = "This is a test email sent via Microsoft Graph API."

        success = send_email(
            to_email=recipient_email,
            subject=subject,
            body=body,
            content_type='HTML'
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f"Email sent successfully to {recipient_email}"))
        else:
            self.stdout.write(self.style.ERROR("Failed to send email. Check logs for details."))
