"""
SMS Service
Handles SMS message sending through various providers (Twilio, AWS SNS, etc.)
"""

from typing import Dict, List, Optional, Any
import requests


class SMSService:
    """Service for sending SMS messages through various providers"""

    def __init__(self, provider: str = "twilio"):
        """
        Initialize SMS service

        Args:
            provider: SMS provider (twilio, aws_sns, vonage, or custom)
        """
        self.provider = provider.lower()

    def send_sms(
        self,
        from_number: str,
        to_numbers: List[str],
        message: str,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS message(s)

        Args:
            from_number: Sender phone number (E.164 format: +1234567890)
            to_numbers: List of recipient phone numbers
            message: SMS message content (max 160 chars for standard SMS)
            account_sid: Twilio account SID (for Twilio)
            auth_token: Twilio auth token (for Twilio)
            api_key: API key for other providers
            api_secret: API secret for other providers

        Returns:
            Dictionary with status, message, and details
        """
        try:
            # Validate inputs
            if not from_number or not to_numbers or not message:
                return {
                    "status": "error",
                    "message": "Missing required fields: from_number, to_numbers, message"
                }

            # Ensure to_numbers is a list
            if isinstance(to_numbers, str):
                to_numbers = [to_numbers]

            # Route to appropriate provider
            if self.provider == "twilio":
                return self._send_twilio(from_number, to_numbers, message, account_sid, auth_token)
            elif self.provider == "aws_sns":
                return self._send_aws_sns(from_number, to_numbers, message, api_key, api_secret)
            elif self.provider == "vonage":
                return self._send_vonage(from_number, to_numbers, message, api_key, api_secret)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported SMS provider: {self.provider}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"SMS sending failed: {str(e)}",
                "error": str(e)
            }

    def _send_twilio(
        self,
        from_number: str,
        to_numbers: List[str],
        message: str,
        account_sid: Optional[str],
        auth_token: Optional[str]
    ) -> Dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            if not account_sid or not auth_token:
                return {
                    "status": "error",
                    "message": "Twilio requires account_sid and auth_token"
                }

            # Twilio REST API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

            sent_count = 0
            failed_count = 0
            results = []

            for to_number in to_numbers:
                try:
                    # Send SMS
                    response = requests.post(
                        url,
                        auth=(account_sid, auth_token),
                        data={
                            "From": from_number,
                            "To": to_number,
                            "Body": message
                        },
                        timeout=10
                    )

                    if response.status_code == 201:
                        sent_count += 1
                        results.append({
                            "to": to_number,
                            "status": "sent",
                            "sid": response.json().get("sid")
                        })
                    else:
                        failed_count += 1
                        results.append({
                            "to": to_number,
                            "status": "failed",
                            "error": response.json().get("message", "Unknown error")
                        })

                except Exception as e:
                    failed_count += 1
                    results.append({
                        "to": to_number,
                        "status": "failed",
                        "error": str(e)
                    })

            if sent_count > 0:
                return {
                    "status": "success" if failed_count == 0 else "partial",
                    "message": f"Sent {sent_count} SMS, {failed_count} failed",
                    "sent": sent_count,
                    "failed": failed_count,
                    "results": results
                }
            else:
                return {
                    "status": "error",
                    "message": "All SMS sends failed",
                    "sent": 0,
                    "failed": failed_count,
                    "results": results
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Twilio SMS error: {str(e)}",
                "error": str(e)
            }

    def _send_aws_sns(
        self,
        from_number: str,
        to_numbers: List[str],
        message: str,
        api_key: Optional[str],
        api_secret: Optional[str]
    ) -> Dict[str, Any]:
        """Send SMS via AWS SNS (requires boto3)"""
        try:
            # Import boto3 dynamically (optional dependency)
            try:
                import boto3
            except ImportError:
                return {
                    "status": "error",
                    "message": "AWS SNS requires 'boto3' package. Install with: pip install boto3"
                }

            if not api_key or not api_secret:
                return {
                    "status": "error",
                    "message": "AWS SNS requires api_key (AWS Access Key) and api_secret (AWS Secret Key)"
                }

            # Create SNS client
            sns_client = boto3.client(
                'sns',
                aws_access_key_id=api_key,
                aws_secret_access_key=api_secret,
                region_name='us-east-1'  # Default region
            )

            sent_count = 0
            failed_count = 0
            results = []

            for to_number in to_numbers:
                try:
                    response = sns_client.publish(
                        PhoneNumber=to_number,
                        Message=message
                    )

                    sent_count += 1
                    results.append({
                        "to": to_number,
                        "status": "sent",
                        "message_id": response.get("MessageId")
                    })

                except Exception as e:
                    failed_count += 1
                    results.append({
                        "to": to_number,
                        "status": "failed",
                        "error": str(e)
                    })

            return {
                "status": "success" if failed_count == 0 else "partial",
                "message": f"Sent {sent_count} SMS via AWS SNS, {failed_count} failed",
                "sent": sent_count,
                "failed": failed_count,
                "results": results
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"AWS SNS error: {str(e)}",
                "error": str(e)
            }

    def _send_vonage(
        self,
        from_number: str,
        to_numbers: List[str],
        message: str,
        api_key: Optional[str],
        api_secret: Optional[str]
    ) -> Dict[str, Any]:
        """Send SMS via Vonage (formerly Nexmo)"""
        try:
            if not api_key or not api_secret:
                return {
                    "status": "error",
                    "message": "Vonage requires api_key and api_secret"
                }

            url = "https://rest.nexmo.com/sms/json"

            sent_count = 0
            failed_count = 0
            results = []

            for to_number in to_numbers:
                try:
                    response = requests.post(
                        url,
                        json={
                            "from": from_number,
                            "to": to_number,
                            "text": message,
                            "api_key": api_key,
                            "api_secret": api_secret
                        },
                        timeout=10
                    )

                    response_data = response.json()
                    messages = response_data.get("messages", [])

                    if messages and messages[0].get("status") == "0":
                        sent_count += 1
                        results.append({
                            "to": to_number,
                            "status": "sent",
                            "message_id": messages[0].get("message-id")
                        })
                    else:
                        failed_count += 1
                        error_text = messages[0].get("error-text", "Unknown error") if messages else "Unknown error"
                        results.append({
                            "to": to_number,
                            "status": "failed",
                            "error": error_text
                        })

                except Exception as e:
                    failed_count += 1
                    results.append({
                        "to": to_number,
                        "status": "failed",
                        "error": str(e)
                    })

            return {
                "status": "success" if failed_count == 0 else "partial",
                "message": f"Sent {sent_count} SMS via Vonage, {failed_count} failed",
                "sent": sent_count,
                "failed": failed_count,
                "results": results
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Vonage SMS error: {str(e)}",
                "error": str(e)
            }

    def validate_config(
        self,
        provider: str,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate SMS provider configuration

        Returns:
            Dictionary with validation status
        """
        try:
            if provider == "twilio":
                if not account_sid or not auth_token:
                    return {
                        "status": "error",
                        "message": "Twilio requires account_sid and auth_token"
                    }
                # Could validate by making a test API call
                return {
                    "status": "success",
                    "message": "Twilio configuration is valid"
                }

            elif provider == "aws_sns":
                if not api_key or not api_secret:
                    return {
                        "status": "error",
                        "message": "AWS SNS requires api_key and api_secret"
                    }
                return {
                    "status": "success",
                    "message": "AWS SNS configuration is valid"
                }

            elif provider == "vonage":
                if not api_key or not api_secret:
                    return {
                        "status": "error",
                        "message": "Vonage requires api_key and api_secret"
                    }
                return {
                    "status": "success",
                    "message": "Vonage configuration is valid"
                }

            else:
                return {
                    "status": "error",
                    "message": f"Unsupported SMS provider: {provider}"
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Validation error: {str(e)}"
            }


# Global SMS service instance
sms_service = SMSService()
