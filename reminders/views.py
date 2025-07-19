from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from .models import UserSubscription
from pywebpush import webpush, WebPushException
from django.conf import settings

@login_required
@csrf_exempt  # Revisa si realmente quieres dejarlo así, ideal manejar CSRF correctamente
def save_subscription(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sub, created = UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'endpoint': data.get('endpoint'),
                    'p256dh': data['keys']['p256dh'],
                    'auth': data['keys']['auth'],
                }
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

def send_web_push_notification(user, message):
    try:
        subscription = getattr(user, 'webpush_subscription', None)  # evita error si no existe
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
                "sub": "mailto:tu-email@dominio.com"  # reemplaza con tu correo real
            }
        )
        return True
    except WebPushException as ex:
        print("Error al enviar push:", repr(ex))
        return False

