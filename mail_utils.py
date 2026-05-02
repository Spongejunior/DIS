try:
    from flask_mail import Mail, Message
except ImportError:  # pragma: no cover - runtime fallback when Flask-Mail is unavailable
    Mail = None
    Message = None


class FallbackMail:
    def init_app(self, app):
        return None

    def send(self, message):
        return None


mail = Mail() if Mail is not None else FallbackMail()


def _send_simple_email(app, subject, recipient, body):
    if not recipient:
        return False

    if Message is None:
        app.logger.warning('Flask-Mail is not installed. Skipping email to %s.', recipient)
        return False

    message = Message(
        subject=subject,
        recipients=[recipient],
        body=body,
        sender=app.config.get('MAIL_DEFAULT_SENDER')
    )

    try:
        mail.send(message)
        return True
    except Exception as exc:  # pragma: no cover - depends on SMTP environment
        app.logger.warning('Email delivery failed for %s: %s', recipient, exc)
        return False


def send_approval_email(app, email):
    return _send_simple_email(
        app,
        'Your ChiwetoCare account has been approved',
        email,
        'Hello,\n\nYour ChiwetoCare account has been approved. You can now sign in and access the system.\n\nThank you.'
    )


def send_rejection_email(app, email):
    return _send_simple_email(
        app,
        'Your ChiwetoCare account request was rejected',
        email,
        'Hello,\n\nYour ChiwetoCare account request was reviewed and rejected. Please contact an administrator if you need more information.\n\nThank you.'
    )
