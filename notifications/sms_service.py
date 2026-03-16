"""
SMS Service for Credential Notifications

Placeholder service for sending user credentials via SMS.
Ready for integration with SMS providers like Twilio, MSG91, etc.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSService:
    """
    SMS Service for sending notifications.

    Currently a placeholder that logs messages.
    To enable actual SMS sending:
    1. Set SEND_CREDENTIALS_SMS = True in settings
    2. Configure SMS_PROVIDER and SMS_API_KEY in settings
    3. Implement the actual send method for your provider
    """

    def __init__(self):
        self.enabled = getattr(settings, 'SEND_CREDENTIALS_SMS', False)
        self.provider = getattr(settings, 'SMS_PROVIDER', 'console')

    def send_credentials(self, phone: str, username: str, password: str, name: str = '') -> dict:
        """
        Send login credentials to user via SMS.

        Args:
            phone: User's phone number (with country code)
            username: Generated username
            password: Generated password
            name: User's name for personalization (optional)

        Returns:
            dict with 'success' boolean and 'message' or 'error' key
        """
        greeting = f"Dear {name}," if name else "Dear User,"
        message = (
            f"{greeting}\n"
            f"Your SchoolSync account has been created.\n"
            f"Username: {username}\n"
            f"Password: {password}\n"
            f"Please change your password on first login.\n"
            f"- SchoolSync Team"
        )

        if not self.enabled:
            # Log to console in development
            logger.info(
                f"[SMS PLACEHOLDER] Would send to {phone}:\n{message}"
            )
            return {
                'success': True,
                'message': 'SMS sending disabled (development mode)',
                'would_send_to': phone,
                'content_preview': message[:100] + '...' if len(message) > 100 else message
            }

        # Actual SMS sending would go here
        # Example for Twilio:
        # return self._send_twilio(phone, message)

        # Example for MSG91:
        # return self._send_msg91(phone, message)

        return self._send_console(phone, message)

    def _send_console(self, phone: str, message: str) -> dict:
        """Console/log output for development"""
        logger.info(f"[SMS] Sending to {phone}:\n{message}")
        print(f"\n{'='*50}")
        print(f"SMS to: {phone}")
        print(f"{'='*50}")
        print(message)
        print(f"{'='*50}\n")
        return {'success': True, 'message': 'Logged to console'}

    def _send_twilio(self, phone: str, message: str) -> dict:
        """
        Send SMS via Twilio.

        Requires:
        - TWILIO_ACCOUNT_SID in settings
        - TWILIO_AUTH_TOKEN in settings
        - TWILIO_PHONE_NUMBER in settings
        """
        try:
            # Uncomment and configure when ready:
            # from twilio.rest import Client
            # client = Client(
            #     settings.TWILIO_ACCOUNT_SID,
            #     settings.TWILIO_AUTH_TOKEN
            # )
            # msg = client.messages.create(
            #     body=message,
            #     from_=settings.TWILIO_PHONE_NUMBER,
            #     to=phone
            # )
            # return {'success': True, 'message_sid': msg.sid}
            raise NotImplementedError("Twilio integration not configured")
        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return {'success': False, 'error': str(e)}

    def _send_msg91(self, phone: str, message: str) -> dict:
        """
        Send SMS via MSG91.

        Requires:
        - MSG91_AUTH_KEY in settings
        - MSG91_SENDER_ID in settings
        """
        try:
            # Uncomment and configure when ready:
            # import requests
            # url = "https://api.msg91.com/api/v5/flow/"
            # headers = {
            #     "authkey": settings.MSG91_AUTH_KEY,
            #     "Content-Type": "application/json"
            # }
            # payload = {
            #     "sender": settings.MSG91_SENDER_ID,
            #     "mobiles": phone,
            #     "message": message
            # }
            # response = requests.post(url, json=payload, headers=headers)
            # return {'success': response.ok, 'response': response.json()}
            raise NotImplementedError("MSG91 integration not configured")
        except Exception as e:
            logger.error(f"MSG91 SMS failed: {e}")
            return {'success': False, 'error': str(e)}

    def send_bulk_credentials(self, users: list) -> dict:
        """
        Send credentials to multiple users.

        Args:
            users: List of dicts with 'phone', 'username', 'password', 'name' keys

        Returns:
            dict with 'total', 'success', 'failed' counts and 'results' list
        """
        results = []
        success_count = 0
        failed_count = 0

        for user in users:
            result = self.send_credentials(
                phone=user.get('phone', ''),
                username=user.get('username', ''),
                password=user.get('password', ''),
                name=user.get('name', '')
            )
            results.append({
                'phone': user.get('phone'),
                'username': user.get('username'),
                **result
            })
            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1

        return {
            'total': len(users),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }


# Singleton instance for easy import
sms_service = SMSService()
