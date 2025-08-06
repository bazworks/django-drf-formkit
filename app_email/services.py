from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from .tasks import send_email_task


class EmailService:
    @staticmethod
    def send_email(
        subject: str,
        recipients: List[str],
        template_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        from_email: Optional[str] = None,
        async_send: bool = True,
    ) -> bool:
        """
        Send an email using either a template or plain text

        Args:
            subject: Email subject
            recipients: List of email addresses
            template_name: Optional HTML template path
            context: Optional context dictionary for template rendering
            text_content: Optional plain text content
            attachments: Optional list of attachment dictionaries
            from_email: Optional sender email
            async_send: Whether to send email asynchronously using Celery

        Returns:
            bool: True if email was queued/sent successfully
        """
        # Add logo URL to context if not present
        if context is None:
            context = {}
        if "logo_url" not in context:
            context["logo_url"] = staticfiles_storage.url("images/logo.png")

        if "company_name" not in context:
            context["company_name"] = (
                settings.COMPANY_NAME if settings.COMPANY_NAME else "Dummy"
            )

        if "support_email" not in context:
            context["support_email"] = (
                settings.DEFAULT_FROM_EMAIL
                if settings.DEFAULT_FROM_EMAIL
                else "support@example.com"
            )

        if async_send:
            send_email_task.delay(
                subject=subject,
                recipients=recipients,
                template_name=template_name,
                context=context,
                text_content=text_content,
                attachments=attachments,
                from_email=from_email,
            )
            return True

        return send_email_task(
            subject=subject,
            recipients=recipients,
            template_name=template_name,
            context=context,
            text_content=text_content,
            attachments=attachments,
            from_email=from_email,
        )

    @classmethod
    def send_password_reset(cls, email: str, reset_url: str) -> bool:
        """
        Send password reset email
        """
        return cls.send_email(
            subject="Password Reset Request",
            recipients=[email],
            template_name="emails/password_reset.html",
            context={"reset_url": reset_url},
        )

    # Add more specific email methods as needed...
