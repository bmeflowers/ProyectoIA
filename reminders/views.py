from django.shortcuts import render
from django.http import JsonResponse
from webpush import push_user

def save_subscription(request):
    if request.method == 'POST':
        push_info = request.POST.dict()
        push_info.pop('csrfmiddlewaretoken') # Elimina el token CSRF
        request.user.webpush_subscription.update_or_create(**push_info)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})

def send_web_push_notification(user, message):
    try:
        push_user(user=user, message=message)
    except Exception as e:
        # Maneja los errores (ej: usuario sin suscripción)
        print(f"Error al enviar push: {e}")