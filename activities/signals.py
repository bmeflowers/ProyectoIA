from django.db.models.signals import post_save
from django.dispatch import receiver
from activities.models import Actividad
from reminders.tasks import send_reminder_email
from django.utils import timezone

@receiver(post_save, sender=Actividad)
def schedule_reminder(sender, instance, created, **kwargs):
    if created and instance.fecha_limite and instance.hora_habito:
        # Calcula el tiempo para el recordatorio (ej: 1 hora antes)
        reminder_time = timezone.datetime.combine(instance.fecha_limite, instance.hora_habito) - timezone.timedelta(hours=1)
        send_reminder_email.apply_async(
            args=[instance.user.id, instance.nombre, instance.id],
            eta=reminder_time
        )