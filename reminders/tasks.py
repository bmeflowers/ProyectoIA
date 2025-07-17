from celery import shared_task
from django.contrib.auth.models import User
from reminders.utils import send_email_notification, create_and_send_notification
from activities.models import Actividad, RegistroHabito
from django.utils import timezone

@shared_task
def send_reminder_email(user_id, activity_name, activity_id):
    user = User.objects.get(pk=user_id)
    subject = f'Recordatorio: {activity_name}'
    message = f'No olvides tu actividad: {activity_name}. ¡Es hora!'
    create_and_send_notification(user, message, 'reminder')
    send_email_notification(user, subject, message)

@shared_task
def check_and_notify_low_activity():
    hoy = timezone.localdate()
    for user in User.objects.all():
        habitos_pendientes = Actividad.objects.filter(user=user, tipo='habito', fecha_limite__lte=hoy, estado='pendiente')
        if habitos_pendientes.exists():
            message = f'¡Parece que tienes hábitos pendientes! Intenta ponerte al día.'
            create_and_send_notification(user, message, 'low_activity')
            send_email_notification(user, 'Hábitos Pendientes', message)

@shared_task
def send_general_notification(user_id, message):
    user = User.objects.get(pk=user_id)
    create_and_send_notification(user, message, 'general')
    send_email_notification(user, 'Notificación', message)