from django.core.mail import send_mail
from django.template.loader import render_to_string
from reminders.models import Notification
from reminders.views import send_web_push_notification

def send_email_notification(user, subject, message, template_name=None, context=None):
    if template_name:
        message = render_to_string(template_name, context)
    send_mail(subject, message, from_email=None, recipient_list=[user.email])

def create_and_send_notification(user, message, notification_type):
    notification = Notification.objects.create(user=user, message=message, notification_type=notification_type)
    # Intenta enviar web push, si falla, solo crea la entrada en la base de datos
    send_web_push_notification(user, message)
    return notification