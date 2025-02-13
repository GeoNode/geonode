import msal
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

class MicrosoftGraphEmailBackend(BaseEmailBackend):
    """
    A Django email backend that sends emails using the Microsoft Graph API.
    """
    def __init__(self, fail_silently=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_silently = fail_silently
        logger.debug("MicrosoftGraphEmailBackend initialized with fail_silently=%s", self.fail_silently)

    def get_access_token(self):
        """
        Authenticate and retrieve an access token from Microsoft Graph API.
        """
        try:
            authority = f"https://login.microsoftonline.com/{settings.GRAPH_API_CREDENTIALS['tenant_id']}"

            # MSAL client application with optional token caching
            app = msal.ConfidentialClientApplication(
                client_id=settings.GRAPH_API_CREDENTIALS['client_id'],
                client_credential=settings.GRAPH_API_CREDENTIALS['client_secret'],
                authority=authority,
                token_cache=msal.SerializableTokenCache()  # Enable token caching for better performance
            )
            scopes = ["https://graph.microsoft.com/.default"]

            logger.debug("Attempting to acquire token silently.")
            # Attempt silent token acquisition
            result = app.acquire_token_silent(scopes, account=None)
            if not result:
                logger.info("Silent token acquisition failed. Attempting to acquire a new token.")
                result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                logger.debug("Access token retrieved successfully.")
                return result["access_token"]

            # Log failure
            logger.error(f"Failed to retrieve access token: {result}")
            if not self.fail_silently:
                raise Exception("Unable to retrieve access token for Microsoft Graph API.")
        except Exception as e:
            logger.exception("An error occurred while retrieving the access token.")
            if not self.fail_silently:
                raise e
        return None

    def send_messages(self, email_messages):
        """
        Send multiple email messages using Microsoft Graph API.
        """
        logger.debug("Fetching access token to send emails.")
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Access token is missing. Emails cannot be sent.")
            return 0

        sent_count = 0
        for email in email_messages:
            logger.debug("Sending email to: %s", email.to)
            if self._send_email(email, access_token):
                sent_count += 1
        logger.debug("Total emails sent: %d", sent_count)
        return sent_count

    def _send_email(self, email: EmailMessage, access_token: str):
        """
        Send a single email using Microsoft Graph API.
        """
        endpoint = f"https://graph.microsoft.com/v1.0/users/{settings.GRAPH_API_CREDENTIALS['mail_from']}/sendMail"
        email_msg = {
            'message': {
                'subject': email.subject,  # Subject of the email
                'body': {
                    'contentType': "HTML",  # Specify the format of the email body
                    'content': email.body  # The actual email content
                },
                'toRecipients': [{'emailAddress': {'address': addr}} for addr in email.to],  # List of recipients
                'ccRecipients': [{'emailAddress': {'address': addr}} for addr in email.cc or []],  # CC recipients
                'bccRecipients': [{'emailAddress': {'address': addr}} for addr in email.bcc or []],  # BCC recipients
            },
            'saveToSentItems': 'true'  # Save the email to the "Sent Items" folder
        }

        try:
            logger.debug("Making POST request to Microsoft Graph API endpoint.")
            response = requests.post(
                endpoint,
                headers={'Authorization': f'Bearer {access_token}'},  # Authorization header with access token
                json=email_msg,  # Email message payload
                timeout=10  # Timeout in seconds
            )
            if response.ok:
                logger.info(f"Email to {email.to} sent successfully.")
                return True
            logger.error(f"Failed to send email: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.exception(f"An exception occurred while sending the email: {e}")

        if not self.fail_silently:
            raise Exception("Failed to send email using Microsoft Graph API.")
        return False

    def send_messages_with_retries(self, email_messages, retries=3):
        """
        Send multiple email messages with retry logic for better reliability.
        """
        sent_count = 0
        for email in email_messages:
            attempt = 0
            while attempt < retries:
                try:
                    logger.debug("Attempt %d to send email to: %s", attempt + 1, email.to)
                    if self._send_email(email, self.get_access_token()):
                        sent_count += 1
                        break
                except Exception as e:
                    logger.warning("Retry %d failed for email to %s: %s", attempt + 1, email.to, str(e))
                    attempt += 1
        logger.debug("Total emails sent after retries: %d", sent_count)
        return sent_count
