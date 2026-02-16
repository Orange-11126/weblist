from flask_mail import Mail, Message
from flask import current_app, render_template

mail = Mail()


def init_mail(app):
    mail.init_app(app)


def send_email(to, subject, template, **kwargs):
    msg = Message(
        subject,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
        recipients=[to]
    )
    msg.html = render_template(template, **kwargs)
    mail.send(msg)


def send_verification_email(user, verification_url):
    subject = '请验证您的邮箱'
    send_email(
        user.email,
        subject,
        'email/verification.html',
        user=user,
        verification_url=verification_url
    )


def send_password_reset_email(user, reset_url):
    subject = '密码重置请求'
    send_email(
        user.email,
        subject,
        'email/password_reset.html',
        user=user,
        reset_url=reset_url
    )


def send_welcome_email(user):
    subject = '欢迎加入我们！'
    send_email(
        user.email,
        subject,
        'email/welcome.html',
        user=user
    )
