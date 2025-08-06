import logging
import os
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.engine import Engine
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def debug_template_dirs():
    """Helper function to print template directories"""

    engine = Engine.get_default()
    print("\nTemplate Dirs:", engine.dirs)
    print("\nBase Dir:", settings.BASE_DIR)
    print(
        "\nTemplate path being searched:",
        os.path.join(settings.BASE_DIR, "templates/emails/password_reset.html"),
    )
    print(
        "\nDoes file exist?:",
        os.path.exists(
            os.path.join(settings.BASE_DIR, "templates/emails/password_reset.html")
        ),
    )


@shared_task
def send_email_task(
    subject: str,
    recipients: List[str],
    template_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    text_content: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    from_email: Optional[str] = None,
) -> bool:
    """
    Celery task to send emails asynchronously

    Args:
        subject: Email subject
        recipients: List of email addresses
        template_name: Optional HTML template path
        context: Optional context dictionary for template rendering
        text_content: Optional plain text content (used if no template)
        attachments: Optional list of attachment dictionaries
        from_email: Optional sender email (falls back to DEFAULT_FROM_EMAIL)

    Returns:
        bool: True if email was sent successfully
    """
    try:
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        context = context or {}

        print("Template name:", template_name)
        print("Context:", context)

        if template_name:
            try:
                # HTML email with template
                html_content = render_to_string(template_name, context)
            except TemplateDoesNotExist as e:
                print(f"Template not found: {template_name}")
                print(f"Error: {str(e)}")
                raise

            # Create plain text version from HTML

            soup = BeautifulSoup(html_content, "html.parser")
            text_content = soup.get_text()

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content or "",
                from_email=from_email,
                to=recipients,
            )
            msg.attach_alternative(html_content, "text/html")
        else:
            # Plain text email
            msg = EmailMessage(
                subject=subject, body=text_content, from_email=from_email, to=recipients
            )

        # Add attachments if any
        if attachments:
            for attachment in attachments:
                msg.attach(
                    filename=attachment["filename"],
                    content=attachment["content"],
                    mimetype=attachment.get("mimetype", "application/octet-stream"),
                )

        msg.send()
        logger.info("Email sent successfully to %s", recipients)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", recipients, str(e))
        return False
