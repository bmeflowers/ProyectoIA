from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from activities.models import Actividad
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .chatbot import obtener_respuesta
from django.conf import settings

from webpush import send_user_notification
import json

def send_push_notification(user, title, body):
    payload = {
        "head": title,
        "body": body,
        "icon": "/static/icons/notification-icon.png",
    }
    send_user_notification(user=user, payload=json.dumps(payload), ttl=1000)


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def test_notification(request):
    send_push_notification(request.user, "¡Hola!", "Notificación de prueba desde WebPush")
    return redirect('dashboard')

@login_required
def test_push_status(request):
    """Vista para probar el estado de las suscripciones push"""
    try:
        print("=== INICIANDO test_push_status ===")
        from webpush.models import PushInformation
        
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            print("Usuario no autenticado")
            return JsonResponse({
                'status': 'error',
                'message': 'Usuario no autenticado'
            }, status=401)
        
        push_info = PushInformation.objects.filter(user=request.user).first()
        print(f"PushInfo encontrado: {push_info}")
        
        if push_info and push_info.subscription:
            print(f"SubscriptionInfo: {push_info.subscription}")
            
            # Obtener campos disponibles de forma segura
            try:
                fields = [field.name for field in push_info.subscription._meta.fields]
                print(f"Campos disponibles: {fields}")
            except Exception as field_error:
                print(f"Error al obtener campos: {field_error}")
                fields = []
            
            # Crear diccionario con valores por defecto seguros
            subscription_data = {
                'id': getattr(push_info.subscription, 'id', 'unknown'),
                'browser': getattr(push_info.subscription, 'browser', 'unknown'),
                'endpoint': getattr(push_info.subscription, 'endpoint', 'unknown'),
                'auth': getattr(push_info.subscription, 'auth', 'unknown'),
                'p256dh': getattr(push_info.subscription, 'p256dh', 'unknown'),
                'user_agent': getattr(push_info.subscription, 'user_agent', 'unknown'),
            }
            
            print(f"Subscription data: {subscription_data}")
            print("=== test_push_status EXITOSO ===")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Usuario tiene suscripción push',
                'subscription': subscription_data
            })
        else:
            print("No se encontró PushInfo o SubscriptionInfo")
            print("=== test_push_status - SIN SUSCRIPCIÓN ===")
            return JsonResponse({
                'status': 'warning',
                'message': 'Usuario no tiene suscripción push'
            })
    except Exception as e:
        print(f"Error en test_push_status: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("=== test_push_status FALLÓ ===")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al verificar estado: {str(e)}'
        }, status=500)

@login_required
def test_vapid_keys(request):
    """Vista para probar las claves VAPID"""
    from py_vapid import Vapid
    
    try:
        # Generar nuevas claves VAPID
        vapid = Vapid()
        vapid.generate_keys()
        
        # Obtener las claves en formato string
        public_key = vapid.public_key.decode('utf-8') if hasattr(vapid.public_key, 'decode') else str(vapid.public_key)
        private_key = vapid.private_key.decode('utf-8') if hasattr(vapid.private_key, 'decode') else str(vapid.private_key)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Claves VAPID generadas correctamente',
            'public_key': public_key,
            'private_key': private_key,
            'public_key_length': len(public_key),
            'private_key_length': len(private_key)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error con las claves VAPID: {str(e)}'
        })

@login_required
def test_simple(request):
    """Vista de prueba simple"""
    return JsonResponse({
        'status': 'success',
        'message': 'Servidor funcionando correctamente',
        'user': str(request.user)
    })

@csrf_exempt
@require_POST
@login_required
def save_push_subscription(request):
    """Vista personalizada para guardar suscripciones push"""
    print("=== INICIANDO save_push_subscription ===")
    try:
        print(f"Usuario autenticado: {request.user}")
        print(f"Body de la request: {request.body}")
        
        data = json.loads(request.body)
        subscription_data = data.get('subscription', {})
        
        print(f"Datos recibidos: {data}")
        print(f"Suscripción: {subscription_data}")
        
        # Guardar la suscripción en el modelo de webpush
        from webpush.models import PushInformation, SubscriptionInfo
        
        # Eliminar suscripciones anteriores del usuario
        deleted_count = PushInformation.objects.filter(user=request.user).delete()[0]
        print(f"Suscripciones eliminadas: {deleted_count}")
        
        # Extraer datos de la suscripción
        endpoint = subscription_data.get('endpoint', '')
        keys = subscription_data.get('keys', {})
        auth = keys.get('auth', '')
        p256dh = keys.get('p256dh', '')
        browser = data.get('browser', 'chrome')
        user_agent = data.get('user_agent', '')
        
        print(f"Endpoint: {endpoint}")
        print(f"Auth: {auth}")
        print(f"P256dh: {p256dh}")
        print(f"Browser: {browser}")
        print(f"User Agent: {user_agent}")
        
        # Crear objeto SubscriptionInfo con los campos correctos
        subscription_info = SubscriptionInfo.objects.create(
            browser=browser,
            user_agent=user_agent,
            endpoint=endpoint,
            auth=auth,
            p256dh=p256dh
        )
        
        print(f"SubscriptionInfo creado: {subscription_info.id}")
        
        # Crear nueva suscripción - manejar el campo group correctamente
        push_data = {
            'user': request.user,
            'subscription': subscription_info,
        }
        
        # Solo agregar group si no está vacío
        group_value = data.get('group', '')
        if group_value and group_value.strip():
            push_data['group'] = group_value
        
        push_info = PushInformation.objects.create(**push_data)
        
        print(f"PushInformation creado: {push_info.id}")
        print("=== save_push_subscription EXITOSO ===")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Suscripción guardada exitosamente'
        })
    except Exception as e:
        print(f"Error en save_push_subscription: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("=== save_push_subscription FALLÓ ===")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al guardar suscripción: {str(e)}'
        }, status=400)


@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body)
        mensaje = data.get("mensaje", "").strip()
        if not mensaje:
            return JsonResponse({"error": "No se envió ningún mensaje."}, status=400)

        respuesta = obtener_respuesta(mensaje)
        return JsonResponse({"respuesta": respuesta})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def enviar_notificacion_automatica(user, titulo, mensaje, datos_adicionales=None):
    """Envía notificación push automática al usuario"""
    try:
        from webpush.models import PushInformation
        from webpush import send_user_notification
        import json
        
        # Verificar si el usuario tiene suscripción push válida
        push_info = PushInformation.objects.filter(user=user).first()
        
        if not push_info or 'development-simulation' in push_info.subscription.endpoint:
            print(f"Notificación automática (desarrollo): {titulo}")
            return False
        
        # Crear payload para la notificación
        payload = {
            "head": titulo,
            "body": mensaje,
            "icon": "/static/images/SOULTRACK-ICON.png",
            "data": datos_adicionales or {}
        }
        
        # Enviar notificación
        send_user_notification(user=user, payload=json.dumps(payload), ttl=1000)
        print(f"Notificación automática enviada: {titulo}")
        return True
        
    except Exception as e:
        print(f"Error al enviar notificación automática: {str(e)}")
        return False

def verificar_y_notificar_habitos():
    """Función que se ejecuta automáticamente para verificar y notificar hábitos"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Obtener todos los usuarios
    usuarios = User.objects.all()
    
    for usuario in usuarios:
        try:
            # Generar notificaciones inteligentes para el usuario
            notificaciones = generar_notificaciones_inteligentes(usuario)
            
            if notificaciones:
                # Enviar la notificación más prioritaria
                notificacion_principal = max(notificaciones, key=lambda x: {
                    'alta': 3, 'media': 2, 'baja': 1
                }[x['prioridad']])
                
                # Enviar notificación automática
                enviar_notificacion_automatica(
                    user=usuario,
                    titulo=notificacion_principal['titulo'],
                    mensaje=notificacion_principal['mensaje'],
                    datos_adicionales={
                        'tipo': notificacion_principal['tipo'],
                        'habito_id': notificacion_principal.get('habito_id'),
                        'actividad_id': notificacion_principal.get('actividad_id'),
                        'porcentaje': notificacion_principal.get('porcentaje')
                    }
                )
                
        except Exception as e:
            print(f"Error al procesar notificaciones para usuario {usuario.username}: {str(e)}")

@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # Obtener hábitos reales del usuario
    habitos = Actividad.objects.filter(user=request.user, tipo='habito').order_by('-fecha_creacion')
    tareas = Actividad.objects.filter(user=request.user, tipo='tarea').order_by('-fecha_creacion')
    
    # Calcular estadísticas de hábitos
    total_habitos = habitos.count()
    habitos_completados = 0
    habitos_pendientes = []
    
    print(f"=== DEBUG DASHBOARD ===")
    print(f"Usuario: {request.user.username}")
    print(f"Total hábitos: {total_habitos}")
    print(f"Query habitos: {habitos.query}")
    
    for habito in habitos:
        registro_hoy = RegistroHabito.objects.filter(
            habito=habito,
            fecha=today
        ).first()
        
        print(f"Hábito: {habito.nombre} - Registro hoy: {'Sí' if registro_hoy else 'No'}")
        
        if registro_hoy:
            habitos_completados += 1
        else:
            habitos_pendientes.append(habito)
    
    porcentaje_completado = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
    
    print(f"Hábitos completados: {habitos_completados}")
    print(f"Hábitos pendientes: {len(habitos_pendientes)}")
    print(f"Porcentaje completado: {porcentaje_completado}%")
    print(f"Lista de hábitos: {[h.nombre for h in habitos]}")
    print(f"Lista de hábitos pendientes: {[h.nombre for h in habitos_pendientes]}")
    print(f"=== FIN DEBUG ===")
    
    # Enviar notificación motivacional al entrar al dashboard
    # Solo enviar si el usuario tiene suscripción push
    from webpush.models import PushInformation
    push_info = PushInformation.objects.filter(user=request.user).first()
    
    if push_info:
        # Enviar notificación motivacional de forma asíncrona
        import threading
        def enviar_motivacion():
            enviar_notificacion_motivacional(request.user)
        
        # Ejecutar en un hilo separado para no bloquear la respuesta
        thread = threading.Thread(target=enviar_motivacion)
        thread.daemon = True
        thread.start()
    
    context = {
        'today': today,
        'habitos': habitos,
        'tareas': tareas,
        'total_habitos': total_habitos,
        'habitos_completados': habitos_completados,
        'habitos_pendientes': habitos_pendientes,
        'porcentaje_completado': porcentaje_completado,
        'vapid_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY'],
    }
    
    print(f"Context enviado al template: {context}")
    
    return render(request, 'dashboard.html', context)

@login_required
def clear_development_subscription(request):
    """Vista para limpiar suscripciones de desarrollo"""
    try:
        print("=== INICIANDO clear_development_subscription ===")
        from webpush.models import PushInformation
        
        # Buscar y eliminar suscripciones de desarrollo
        deleted_count = PushInformation.objects.filter(
            user=request.user,
            subscription__endpoint__contains='development-simulation'
        ).delete()[0]
        
        print(f"Suscripciones eliminadas: {deleted_count}")
        print("=== clear_development_subscription EXITOSO ===")
        
        if deleted_count > 0:
            return JsonResponse({
                'status': 'success',
                'message': f'Suscripción de desarrollo eliminada. Puedes crear una nueva suscripción.'
            })
        else:
            return JsonResponse({
                'status': 'warning',
                'message': 'No se encontraron suscripciones de desarrollo para eliminar.'
            })
    except Exception as e:
        print(f"Error en clear_development_subscription: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        print("=== clear_development_subscription FALLÓ ===")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al limpiar suscripción: {str(e)}'
        }, status=500)


from django.utils import timezone
from datetime import datetime, timedelta
from activities.models import Actividad, RegistroHabito

def verificar_habitos_pendientes(user):
    """Verifica hábitos no completados y porcentajes de logro"""
    today = timezone.now().date()
    notificaciones = []
    
    # Obtener todos los hábitos del usuario
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    
    for habito in habitos:
        # Verificar si el hábito fue completado hoy
        registro_hoy = RegistroHabito.objects.filter(
            habito=habito,
            fecha=today
        ).first()
        
        if not registro_hoy:
            # Hábito no completado hoy
            notificaciones.append({
                'tipo': 'habito_pendiente',
                'titulo': '¡Hábito pendiente!',
                'mensaje': f'No has completado tu hábito "{habito.nombre}" hoy. ¡No dejes que se rompa tu racha!',
                'habito_id': habito.id,
                'prioridad': 'alta'
            })
        else:
            # Verificar porcentaje de logro
            if hasattr(habito, 'meta') and habito.meta:
                try:
                    meta_valor = float(habito.meta)
                    if registro_hoy.valor < meta_valor:
                        porcentaje = (registro_hoy.valor / meta_valor) * 100
                        notificaciones.append({
                            'tipo': 'meta_baja',
                            'titulo': 'Meta por debajo del objetivo',
                            'mensaje': f'Tu hábito "{habito.nombre}" está al {porcentaje:.1f}% de tu meta. ¡Sigue esforzándote!',
                            'habito_id': habito.id,
                            'porcentaje': porcentaje,
                            'prioridad': 'media'
                        })
                except (ValueError, TypeError):
                    pass
    
    return notificaciones

def verificar_actividades_inactivas(user):
    """Verifica actividades que no se han realizado recientemente"""
    today = timezone.now().date()
    notificaciones = []
    
    # Obtener actividades que no se han registrado en los últimos 3 días
    fecha_limite = today - timedelta(days=3)
    
    actividades = Actividad.objects.filter(user=user)
    
    for actividad in actividades:
        ultimo_registro = RegistroHabito.objects.filter(
            habito=actividad
        ).order_by('-fecha').first()
        
        if not ultimo_registro or ultimo_registro.fecha < fecha_limite:
            notificaciones.append({
                'tipo': 'actividad_inactiva',
                'titulo': '¡Actividad olvidada!',
                'mensaje': f'No has registrado tu actividad "{actividad.nombre}" en varios días. ¡Es momento de retomarla!',
                'actividad_id': actividad.id,
                'prioridad': 'media'
            })
    
    return notificaciones

def generar_notificaciones_inteligentes(user):
    """Genera notificaciones inteligentes basadas en el comportamiento del usuario"""
    notificaciones = []
    
    # Verificar hábitos pendientes
    notificaciones.extend(verificar_habitos_pendientes(user))
    
    # Verificar actividades inactivas
    notificaciones.extend(verificar_actividades_inactivas(user))
    
    # Agregar notificación motivacional si no hay hábitos
    habitos = Actividad.objects.filter(user=user, tipo='habito').count()
    if habitos == 0:
        notificaciones.append({
            'tipo': 'sin_habitos',
            'titulo': '¡Comienza tu viaje!',
            'mensaje': 'Aún no tienes hábitos registrados. ¡Crea tu primer hábito y comienza a transformar tu vida!',
            'prioridad': 'baja'
        })
    
    return notificaciones

@login_required
def enviar_notificacion_inteligente(request):
    """Vista para enviar notificaciones inteligentes basadas en el comportamiento del usuario"""
    try:
        # Generar notificaciones inteligentes
        notificaciones = generar_notificaciones_inteligentes(request.user)
        
        if not notificaciones:
            return JsonResponse({
                'status': 'success',
                'message': '¡Excelente! Todos tus hábitos están al día.',
                'notificaciones': []
            })
        
        # Enviar la notificación más prioritaria
        notificacion_principal = max(notificaciones, key=lambda x: {
            'alta': 3, 'media': 2, 'baja': 1
        }[x['prioridad']])
        
        # Crear payload para la notificación
        payload = {
            "head": notificacion_principal['titulo'],
            "body": notificacion_principal['mensaje'],
            "icon": "/static/images/SOULTRACK-ICON.png",
            "data": {
                "tipo": notificacion_principal['tipo'],
                "habito_id": notificacion_principal.get('habito_id'),
                "actividad_id": notificacion_principal.get('actividad_id'),
                "porcentaje": notificacion_principal.get('porcentaje')
            }
        }
        
        # Verificar si el usuario tiene suscripción push
        from webpush.models import PushInformation
        push_info = PushInformation.objects.filter(user=request.user).first()
        
        if push_info and 'development-simulation' not in push_info.subscription.endpoint:
            # Enviar notificación real
            from webpush import send_user_notification
            import json
            send_user_notification(user=request.user, payload=json.dumps(payload), ttl=1000)
            print(f"Notificación inteligente enviada: {notificacion_principal['titulo']}")
        else:
            # Modo desarrollo - solo mostrar mensaje
            print(f"Notificación inteligente (desarrollo): {notificacion_principal['titulo']}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notificación inteligente enviada',
            'notificacion': notificacion_principal,
            'total_pendientes': len(notificaciones)
        })
        
    except Exception as e:
        print(f"Error al enviar notificación inteligente: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al enviar notificación: {str(e)}'
        }, status=500)

@login_required
def obtener_estado_habitos(request):
    """Vista para obtener el estado actual de los hábitos del usuario"""
    try:
        notificaciones = generar_notificaciones_inteligentes(request.user)
        
        # Contar hábitos por estado
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        habitos_completados = 0
        habitos_pendientes = 0
        
        today = timezone.now().date()
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if registro_hoy:
                habitos_completados += 1
            else:
                habitos_pendientes += 1
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'total_habitos': total_habitos,
                'habitos_completados': habitos_completados,
                'habitos_pendientes': habitos_pendientes,
                'notificaciones_pendientes': len(notificaciones),
                'porcentaje_completado': (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al obtener estado: {str(e)}'
        }, status=500)

@login_required
def push_testing(request):
    """Vista para la página de pruebas de notificaciones push"""
    return render(request, 'push_testing.html')

def generar_mensaje_motivacional(user):
    """Genera un mensaje motivacional personalizado basado en el estado del usuario"""
    today = timezone.now().date()
    
    # Obtener estadísticas del usuario
    habitos = Actividad.objects.filter(user=user, tipo='habito')
    total_habitos = habitos.count()
    
    if total_habitos == 0:
        return {
            'titulo': '¡Bienvenido a tu nueva rutina!',
            'mensaje': 'Es el momento perfecto para crear tu primer hábito. ¡Cada gran cambio comienza con un pequeño paso!',
            'tipo': 'bienvenida'
        }
    
    # Contar hábitos completados hoy
    habitos_completados = 0
    for habito in habitos:
        if RegistroHabito.objects.filter(habito=habito, fecha=today).exists():
            habitos_completados += 1
    
    porcentaje = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
    
    # Generar mensaje basado en el progreso
    if porcentaje == 100:
        return {
            'titulo': '¡Día perfecto! 🎉',
            'mensaje': f'¡Increíble! Has completado todos tus {total_habitos} hábitos hoy. ¡Sigues construyendo una versión mejor de ti mismo!',
            'tipo': 'perfecto'
        }
    elif porcentaje >= 70:
        return {
            'titulo': '¡Excelente progreso! ⭐',
            'mensaje': f'Has completado {habitos_completados} de {total_habitos} hábitos. ¡Estás muy cerca de un día perfecto!',
            'tipo': 'buen_progreso'
        }
    elif porcentaje >= 50:
        return {
            'titulo': '¡Sigue así! 💪',
            'mensaje': f'Has completado {habitos_completados} de {total_habitos} hábitos. ¡Cada paso cuenta hacia tu meta!',
            'tipo': 'progreso_medio'
        }
    elif porcentaje > 0:
        return {
            'titulo': '¡Buen comienzo! 🌟',
            'mensaje': f'Has completado {habitos_completados} de {total_habitos} hábitos. ¡Es un gran inicio para el día!',
            'tipo': 'inicio'
        }
    else:
        return {
            'titulo': '¡Es hora de brillar! ✨',
            'mensaje': f'Tienes {total_habitos} hábitos esperando por ti. ¡Hoy es el día perfecto para comenzar!',
            'tipo': 'motivacion'
        }

def enviar_notificacion_motivacional(user):
    """Envía una notificación motivacional al usuario"""
    try:
        # Generar mensaje motivacional
        mensaje = generar_mensaje_motivacional(user)
        
        # Enviar notificación automática
        enviado = enviar_notificacion_automatica(
            user=user,
            titulo=mensaje['titulo'],
            mensaje=mensaje['mensaje'],
            datos_adicionales={
                'tipo': 'motivacional',
                'subtipo': mensaje['tipo'],
                'timestamp': timezone.now().isoformat()
            }
        )
        
        if enviado:
            print(f"Notificación motivacional enviada a {user.username}: {mensaje['titulo']}")
        else:
            print(f"Notificación motivacional (desarrollo): {mensaje['titulo']}")
            
        return True
        
    except Exception as e:
        print(f"Error al enviar notificación motivacional: {str(e)}")
        return False

@login_required
def enviar_notificacion_motivacional_manual(request):
    """Vista para enviar notificación motivacional manualmente (para pruebas)"""
    try:
        # Generar y enviar notificación motivacional
        mensaje = generar_mensaje_motivacional(request.user)
        
        # Verificar si el usuario tiene suscripción push
        from webpush.models import PushInformation
        push_info = PushInformation.objects.filter(user=request.user).first()
        
        if push_info and 'development-simulation' not in push_info.subscription.endpoint:
            # Enviar notificación real
            from webpush import send_user_notification
            import json
            
            payload = {
                "head": mensaje['titulo'],
                "body": mensaje['mensaje'],
                "icon": "/static/images/SOULTRACK-ICON.png",
                "data": {
                    'tipo': 'motivacional',
                    'subtipo': mensaje['tipo'],
                    'timestamp': timezone.now().isoformat()
                }
            }
            
            send_user_notification(user=request.user, payload=json.dumps(payload), ttl=1000)
            print(f"Notificación motivacional enviada: {mensaje['titulo']}")
        else:
            print(f"Notificación motivacional (desarrollo): {mensaje['titulo']}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notificación motivacional enviada',
            'notificacion': mensaje
        })
        
    except Exception as e:
        print(f"Error al enviar notificación motivacional: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error al enviar notificación: {str(e)}'
        }, status=500)

