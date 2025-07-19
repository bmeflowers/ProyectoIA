from django.db import models
from django.contrib.auth.models import User
from pywebpush import webpush, WebPushException
from django.conf import settings

def send_web_push_notification(user, message):
    try:
        subscription = user.webpush_subscription  # OneToOneField
        if not subscription:
            print("El usuario no tiene suscripción.")
            return False

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            }
        }

        webpush(
            subscription_info,
            data=message,
            vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
            vapid_claims={
                "sub": "mailto:tu-email@dominio.com"
            }
        )
        return True
    except WebPushException as ex:
        print("Error al enviar push:", repr(ex))
        return False


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('reminder', 'Recordatorio'),
            ('low_activity', 'Baja Actividad'),
            ('general', 'General')
        ],
        default='general'
    )

    def __str__(self):
        return f'Notificación para {self.user.username} ({self.notification_type}) - {self.sent_at}'

    
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='webpush_subscription')
    endpoint = models.URLField()
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    def __str__(self):
        return f'Suscripción Web Push de {self.user.username}'
