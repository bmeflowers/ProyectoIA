from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from webpush import send_user_notification
from webpush.models import PushInformation
from activities.models import Actividad, RegistroHabito
from django.utils import timezone
import json

@login_required
def dashboard(request):
    today = timezone.localtime(timezone.now()).date()
    
    # Obtener hábitos reales del usuario
    habitos = Actividad.objects.filter(user=request.user, tipo='habito').order_by('-fecha_creacion')
    tareas = Actividad.objects.filter(user=request.user, tipo='tarea').order_by('-fecha_creacion')
    
    # Calcular estadísticas de hábitos
    total_habitos = habitos.count()
    habitos_completados = 0
    habitos_pendientes_ids = []
    
    print(f"=== DEBUG DASHBOARD (reminders) ===")
    print(f"Usuario: {request.user.username}")
    print(f"Total hábitos: {total_habitos}")
    
    for habito in habitos:
        registro_hoy = RegistroHabito.objects.filter(
            habito=habito,
            fecha=today
        ).first()
        
        print(f"Hábito: {habito.nombre} (ID: {habito.id}) - Registro hoy: {'Sí' if registro_hoy else 'No'}")
        if registro_hoy:
            print(f"  - Registro encontrado: {registro_hoy.fecha} - {registro_hoy.habito.nombre}")
            print(f"  - Tipo de fecha registro: {type(registro_hoy.fecha)}")
            print(f"  - Tipo de fecha hoy: {type(today)}")
            print(f"  - Fecha registro: {registro_hoy.fecha}")
            print(f"  - Fecha hoy: {today}")
            print(f"  - ¿Son iguales?: {registro_hoy.fecha == today}")
        else:
            print(f"  - No hay registro para hoy: {today}")
            # Verificar si hay registros para este hábito en otras fechas
            otros_registros = RegistroHabito.objects.filter(habito=habito).order_by('-fecha')[:3]
            if otros_registros:
                print(f"  - Otros registros encontrados:")
                for reg in otros_registros:
                    print(f"    * {reg.fecha} - {reg.habito.nombre}")
            else:
                print(f"  - No hay ningún registro para este hábito")
        
        if registro_hoy:
            habitos_completados += 1
        else:
            habitos_pendientes_ids.append(habito.id)
    
    porcentaje_completado = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
    
    print(f"Hábitos completados: {habitos_completados}")
    print(f"Hábitos pendientes: {len(habitos_pendientes_ids)}")
    print(f"Porcentaje completado: {porcentaje_completado}%")
    print(f"Lista de hábitos: {[h.nombre for h in habitos]}")
    print(f"Lista de IDs pendientes: {habitos_pendientes_ids}")
    print(f"Fecha de hoy: {today}")
    print(f"=== FIN DEBUG ===")
    
    # Enviar notificación motivacional al entrar al dashboard
    # Solo enviar si el usuario tiene suscripción push
    push_info = PushInformation.objects.filter(user=request.user).first()
    
    if push_info:
        # Enviar notificación motivacional de forma asíncrona
        import threading
        def enviar_motivacion():
            # Importar la función desde mysite.views
            from mysite.views import enviar_notificacion_motivacional
            
            # Determinar el tipo de notificación basado en el progreso
            if total_habitos == 0:
                mensaje = "¡Comienza tu viaje de automejora! 🌟 Crea tu primer hábito para empezar a transformar tu vida."
            elif porcentaje_completado == 100:
                mensaje = "¡Día perfecto! 🎉 Has completado todos tus hábitos. ¡Eres increíble!"
            elif porcentaje_completado >= 80:
                mensaje = f"¡Excelente progreso! 🚀 Has completado {habitos_completados}/{total_habitos} hábitos. ¡Sigue así!"
            elif porcentaje_completado >= 50:
                mensaje = f"¡Buen trabajo! 💪 Has completado {habitos_completados}/{total_habitos} hábitos. ¡Tú puedes con el resto!"
            elif porcentaje_completado > 0:
                mensaje = f"¡Cada paso cuenta! 🌱 Has completado {habitos_completados}/{total_habitos} hábitos. ¡Continúa!"
            else:
                mensaje = "¡Hoy es un nuevo día! 🌅 Tienes {total_habitos} hábitos pendientes. ¡Empieza con uno!"
            
            # Enviar notificación personalizada
            try:
                from webpush import send_user_notification
                import json
                
                payload = {
                    "head": "¡Motivación diaria! 💫",
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                print(f"Notificación personalizada enviada: {mensaje}")
                
            except Exception as e:
                print(f"Error enviando notificación personalizada: {str(e)}")
        
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
        'habitos_pendientes': habitos_pendientes_ids,
        'porcentaje_completado': porcentaje_completado,
        'vapid_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY'],
    }
    
    print(f"Context enviado al template: {context}")
    
    return render(request, 'dashboard.html', context)

@login_required
def enviar_recordatorio_habitos_pendientes(request):
    """Envía recordatorios para hábitos pendientes"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos_pendientes = []
        
        # Obtener hábitos del usuario
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if not registro_hoy:
                habitos_pendientes.append(habito)
        
        if habitos_pendientes:
            # Crear mensaje personalizado
            if len(habitos_pendientes) == 1:
                mensaje = f"¡No olvides completar tu hábito: {habitos_pendientes[0].nombre}! ⏰"
            else:
                nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                if len(habitos_pendientes) > 2:
                    nombres += f" y {len(habitos_pendientes) - 2} más"
                mensaje = f"¡Tienes hábitos pendientes: {nombres}! ⏰"
            
            # Enviar notificación solo si hay suscripción válida
            push_info = PushInformation.objects.filter(user=request.user).first()
            
            if push_info:
                try:
                    payload = {
                        "head": "¡Recordatorio de hábitos! ⏰",
                        "body": mensaje,
                        "icon": "/static/images/SOULTRACK-ICON.png"
                    }
                    
                    send_user_notification(
                        user=request.user, 
                        payload=json.dumps(payload), 
                        ttl=1000
                    )
                    
                    print(f"Recordatorio enviado: {mensaje}")
                    return JsonResponse({"status": "success", "message": mensaje})
                    
                except Exception as e:
                    print(f"Error enviando notificación: {str(e)}")
                    # En desarrollo, simular envío exitoso
                    if 'development-simulation' in str(push_info.subscription.endpoint):
                        print("Simulando envío en desarrollo")
                        return JsonResponse({"status": "success", "message": mensaje + " (simulado en desarrollo)"})
                    else:
                        return JsonResponse({"status": "error", "message": f"Error enviando notificación: {str(e)}"})
            else:
                return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push configurada"})
        else:
            return JsonResponse({"status": "no_pending", "message": "No hay hábitos pendientes"})
            
    except Exception as e:
        print(f"Error enviando recordatorio: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_automatica(request):
    """Envía notificaciones automáticas basadas en el estado de los hábitos"""
    try:
        today = timezone.localtime(timezone.now()).date()
        
        # Obtener hábitos del usuario
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        
        if total_habitos == 0:
            return JsonResponse({"status": "no_habits", "message": "No tienes hábitos configurados"})
        
        # Contar hábitos completados y pendientes
        habitos_completados = 0
        habitos_pendientes = []
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if registro_hoy:
                habitos_completados += 1
            else:
                habitos_pendientes.append(habito)
        
        porcentaje_completado = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
        
        # Determinar tipo de notificación automática
        if porcentaje_completado == 100:
            mensaje = "🎉 ¡Día perfecto! Has completado todos tus hábitos. ¡Eres increíble!"
            titulo = "¡Día Perfecto!"
        elif porcentaje_completado >= 80:
            mensaje = f"🚀 ¡Excelente progreso! Has completado {habitos_completados}/{total_habitos} hábitos. ¡Sigue así!"
            titulo = "¡Excelente Progreso!"
        elif porcentaje_completado >= 50:
            mensaje = f"💪 ¡Buen trabajo! Has completado {habitos_completados}/{total_habitos} hábitos. ¡Tú puedes con el resto!"
            titulo = "¡Buen Trabajo!"
        elif porcentaje_completado > 0:
            mensaje = f"🌱 ¡Cada paso cuenta! Has completado {habitos_completados}/{total_habitos} hábitos. ¡Continúa!"
            titulo = "¡Cada Paso Cuenta!"
        else:
            # Si no hay hábitos completados, enviar recordatorio
            if habitos_pendientes:
                if len(habitos_pendientes) == 1:
                    mensaje = f"⏰ ¡No olvides completar tu hábito: {habitos_pendientes[0].nombre}!"
                else:
                    nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                    if len(habitos_pendientes) > 2:
                        nombres += f" y {len(habitos_pendientes) - 2} más"
                    mensaje = f"⏰ ¡Tienes hábitos pendientes: {nombres}!"
                titulo = "¡Recordatorio de Hábitos!"
            else:
                mensaje = "🌟 ¡Comienza tu viaje de automejora! Crea tu primer hábito para empezar a transformar tu vida."
                titulo = "¡Comienza tu Viaje!"
        
        # Enviar notificación automática
        push_info = PushInformation.objects.filter(user=request.user).first()
        
        if push_info:
            try:
                payload = {
                    "head": titulo,
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación automática enviada: {mensaje}")
                return JsonResponse({
                    "status": "success", 
                    "message": mensaje,
                    "porcentaje": porcentaje_completado,
                    "completados": habitos_completados,
                    "total": total_habitos
                })
                
            except Exception as e:
                print(f"Error enviando notificación automática: {str(e)}")
                # En desarrollo, simular envío exitoso
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    print("Simulando envío automático en desarrollo")
                    return JsonResponse({
                        "status": "success", 
                        "message": mensaje + " (simulado en desarrollo)",
                        "porcentaje": porcentaje_completado,
                        "completados": habitos_completados,
                        "total": total_habitos
                    })
                else:
                    return JsonResponse({"status": "error", "message": f"Error enviando notificación: {str(e)}"})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push configurada"})
            
    except Exception as e:
        print(f"Error en notificación automática: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def enviar_notificacion(request):
    try:
        # Verificar si el usuario tiene una suscripción válida
        push_info = PushInformation.objects.filter(user=request.user).first()
        
        if not push_info:
            print("Usuario no tiene suscripción push")
            return redirect('dashboard')
        
        # Verificar si es una suscripción de desarrollo
        if 'development-simulation' in push_info.subscription.endpoint:
            print("Suscripción de desarrollo detectada - no se puede enviar notificación real")
            # En desarrollo, solo mostrar mensaje
            return redirect('dashboard')
        
        payload = {
            "head": "¡Recordatorio!",
            "body": "No registraste tu hábito hoy. ¡Hazlo ahora!",
            "icon": "/static/icons/notification-icon.png",  # opcional
        }
        
        send_user_notification(user=request.user, payload=json.dumps(payload), ttl=1000)
        print("Notificación enviada exitosamente")
        
    except Exception as e:
        print(f"Error al enviar notificación: {str(e)}")
        # En caso de error, no fallar la aplicación
    
    return redirect('dashboard')

@login_required
def notificacion_motivacion_manana(request):
    """Notificación motivacional de la mañana"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        
        if total_habitos == 0:
            return JsonResponse({"status": "no_habits", "message": "No tienes hábitos configurados"})
        
        # Mensajes motivacionales de la mañana
        mensajes_manana = [
            "🌅 ¡Buenos días! Es un nuevo día para ser tu mejor versión. ¡Tú puedes con todo!",
            "☀️ ¡Hola! El sol brilla y tú también brillarás hoy. ¡Empieza tu día con energía!",
            "🌟 ¡Buenos días! Cada mañana es una nueva oportunidad para mejorar. ¡Aprovecha este día!",
            "💪 ¡Hola! Hoy es el día perfecto para avanzar hacia tus metas. ¡Tú tienes el poder!",
            "🌱 ¡Buenos días! Como las plantas que crecen cada día, tú también creces y mejoras constantemente."
        ]
        
        import random
        mensaje = random.choice(mensajes_manana)
        
        # Enviar notificación
        push_info = PushInformation.objects.filter(user=request.user).first()
        if push_info:
            try:
                payload = {
                    "head": "¡Buenos Días! 🌅",
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación matutina enviada: {mensaje}")
                return JsonResponse({"status": "success", "message": mensaje})
                
            except Exception as e:
                print(f"Error enviando notificación matutina: {str(e)}")
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    return JsonResponse({"status": "success", "message": mensaje + " (simulado)"})
                else:
                    return JsonResponse({"status": "error", "message": str(e)})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_recordatorio_mediodia(request):
    """Recordatorio de mediodía para hábitos pendientes"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        habitos_pendientes = []
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if not registro_hoy:
                habitos_pendientes.append(habito)
        
        if habitos_pendientes:
            if len(habitos_pendientes) == 1:
                mensaje = f"⏰ ¡Mediodía! No olvides completar tu hábito: {habitos_pendientes[0].nombre}"
            else:
                nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                if len(habitos_pendientes) > 2:
                    nombres += f" y {len(habitos_pendientes) - 2} más"
                mensaje = f"⏰ ¡Mediodía! Tienes hábitos pendientes: {nombres}"
            
            # Enviar notificación
            push_info = PushInformation.objects.filter(user=request.user).first()
            if push_info:
                try:
                    payload = {
                        "head": "¡Recordatorio de Mediodía! ⏰",
                        "body": mensaje,
                        "icon": "/static/images/SOULTRACK-ICON.png"
                    }
                    
                    send_user_notification(
                        user=request.user, 
                        payload=json.dumps(payload), 
                        ttl=1000
                    )
                    
                    print(f"Recordatorio mediodía enviado: {mensaje}")
                    return JsonResponse({"status": "success", "message": mensaje})
                    
                except Exception as e:
                    print(f"Error enviando recordatorio mediodía: {str(e)}")
                    if 'development-simulation' in str(push_info.subscription.endpoint):
                        return JsonResponse({"status": "success", "message": mensaje + " (simulado)"})
                    else:
                        return JsonResponse({"status": "error", "message": str(e)})
            else:
                return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push"})
        else:
            return JsonResponse({"status": "no_pending", "message": "¡Excelente! Todos tus hábitos están completados"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_motivacion_tarde(request):
    """Notificación motivacional de la tarde"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        habitos_completados = 0
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if registro_hoy:
                habitos_completados += 1
        
        porcentaje = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
        
        # Mensajes motivacionales de la tarde
        if porcentaje >= 80:
            mensajes = [
                "🚀 ¡Increíble progreso! Has completado la mayoría de tus hábitos. ¡Sigue así!",
                "💫 ¡Espectacular! Tu dedicación está dando frutos. ¡Eres una inspiración!",
                "🌟 ¡Excelente trabajo! Has demostrado que puedes lograr lo que te propones."
            ]
        elif porcentaje >= 50:
            mensajes = [
                "💪 ¡Buen trabajo! Has completado más de la mitad de tus hábitos. ¡Continúa!",
                "🌱 ¡Cada paso cuenta! Estás construyendo hábitos sólidos. ¡Sigue adelante!",
                "✨ ¡Progreso notable! Cada hábito completado te acerca a tus metas."
            ]
        else:
            mensajes = [
                "🌅 ¡Aún hay tiempo! La tarde es perfecta para completar tus hábitos pendientes.",
                "💪 ¡Tú puedes! Cada hábito que completes hoy es una victoria.",
                "🌟 ¡No te rindas! Cada pequeño paso te hace más fuerte."
            ]
        
        import random
        mensaje = random.choice(mensajes)
        
        # Enviar notificación
        push_info = PushInformation.objects.filter(user=request.user).first()
        if push_info:
            try:
                payload = {
                    "head": "¡Motivación de Tarde! 🌅",
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación tarde enviada: {mensaje}")
                return JsonResponse({"status": "success", "message": mensaje})
                
            except Exception as e:
                print(f"Error enviando notificación tarde: {str(e)}")
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    return JsonResponse({"status": "success", "message": mensaje + " (simulado)"})
                else:
                    return JsonResponse({"status": "error", "message": str(e)})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_recordatorio_noche(request):
    """Recordatorio final de la noche"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        habitos_pendientes = []
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if not registro_hoy:
                habitos_pendientes.append(habito)
        
        if habitos_pendientes:
            if len(habitos_pendientes) == 1:
                mensaje = f"🌙 ¡Última oportunidad! Completa tu hábito: {habitos_pendientes[0].nombre}"
            else:
                nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                if len(habitos_pendientes) > 2:
                    nombres += f" y {len(habitos_pendientes) - 2} más"
                mensaje = f"🌙 ¡Última oportunidad! Completa tus hábitos: {nombres}"
            
            # Enviar notificación
            push_info = PushInformation.objects.filter(user=request.user).first()
            if push_info:
                try:
                    payload = {
                        "head": "¡Recordatorio Final! 🌙",
                        "body": mensaje,
                        "icon": "/static/images/SOULTRACK-ICON.png"
                    }
                    
                    send_user_notification(
                        user=request.user, 
                        payload=json.dumps(payload), 
                        ttl=1000
                    )
                    
                    print(f"Recordatorio noche enviado: {mensaje}")
                    return JsonResponse({"status": "success", "message": mensaje})
                    
                except Exception as e:
                    print(f"Error enviando recordatorio noche: {str(e)}")
                    if 'development-simulation' in str(push_info.subscription.endpoint):
                        return JsonResponse({"status": "success", "message": mensaje + " (simulado)"})
                    else:
                        return JsonResponse({"status": "error", "message": str(e)})
            else:
                return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push"})
        else:
            return JsonResponse({"status": "no_pending", "message": "¡Perfecto! Todos tus hábitos están completados"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_celebracion(request):
    """Notificación de celebración por logros"""
    try:
        today = timezone.localtime(timezone.now()).date()
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        habitos_completados = 0
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if registro_hoy:
                habitos_completados += 1
        
        porcentaje = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
        
        if porcentaje == 100:
            mensajes = [
                "🎉 ¡PERFECTO! ¡Has completado todos tus hábitos! ¡Eres increíble!",
                "🏆 ¡CAMPEÓN! ¡Día perfecto! Has demostrado que puedes lograr todo lo que te propones!",
                "⭐ ¡ESTRELLA! ¡Has brillado hoy! Todos tus hábitos completados. ¡Eres una inspiración!"
            ]
        elif porcentaje >= 90:
            mensajes = [
                "🌟 ¡CASI PERFECTO! ¡Has completado casi todos tus hábitos! ¡Eres asombroso!",
                "💫 ¡EXCELENTE! ¡Has logrado un progreso excepcional! ¡Sigue así!",
                "✨ ¡INCREÍBLE! ¡Has demostrado una dedicación extraordinaria!"
            ]
        else:
            return JsonResponse({"status": "no_celebration", "message": "Aún no hay logros para celebrar"})
        
        import random
        mensaje = random.choice(mensajes)
        
        # Enviar notificación
        push_info = PushInformation.objects.filter(user=request.user).first()
        if push_info:
            try:
                payload = {
                    "head": "¡CELEBRACIÓN! 🎉",
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación celebración enviada: {mensaje}")
                return JsonResponse({"status": "success", "message": mensaje})
                
            except Exception as e:
                print(f"Error enviando notificación celebración: {str(e)}")
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    return JsonResponse({"status": "success", "message": mensaje + " (simulado)"})
                else:
                    return JsonResponse({"status": "error", "message": str(e)})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_automatica_por_horario(request):
    """Envía notificaciones automáticas según la hora del día"""
    try:
        from datetime import datetime
        now = timezone.localtime(timezone.now())
        hora_actual = now.hour
        today = now.date()
        
        print(f"=== NOTIFICACIÓN AUTOMÁTICA POR HORARIO ===")
        print(f"Hora actual: {hora_actual}:{now.minute}")
        print(f"Fecha: {today}")
        
        # Obtener hábitos del usuario
        habitos = Actividad.objects.filter(user=request.user, tipo='habito')
        total_habitos = habitos.count()
        
        if total_habitos == 0:
            return JsonResponse({"status": "no_habits", "message": "No tienes hábitos configurados"})
        
        # Contar hábitos completados y pendientes
        habitos_completados = 0
        habitos_pendientes = []
        
        for habito in habitos:
            registro_hoy = RegistroHabito.objects.filter(
                habito=habito,
                fecha=today
            ).first()
            
            if registro_hoy:
                habitos_completados += 1
            else:
                habitos_pendientes.append(habito)
        
        porcentaje_completado = (habitos_completados / total_habitos * 100) if total_habitos > 0 else 0
        
        # Determinar tipo de notificación según la hora
        if 6 <= hora_actual <= 9:  # Mañana temprana (6-9 AM)
            tipo_notificacion = "motivacion_manana"
            mensajes = [
                "🌅 ¡Buenos días! Es un nuevo día para ser tu mejor versión. ¡Tú puedes con todo!",
                "☀️ ¡Hola! El sol brilla y tú también brillarás hoy. ¡Empieza tu día con energía!",
                "🌟 ¡Buenos días! Cada mañana es una nueva oportunidad para mejorar. ¡Aprovecha este día!",
                "💪 ¡Hola! Hoy es el día perfecto para avanzar hacia tus metas. ¡Tú tienes el poder!",
                "🌱 ¡Buenos días! Como las plantas que crecen cada día, tú también creces y mejoras constantemente."
            ]
            titulo = "¡Buenos Días! 🌅"
            
        elif 10 <= hora_actual <= 12:  # Mañana media (10-12 AM)
            tipo_notificacion = "recordatorio_manana"
            if habitos_pendientes:
                if len(habitos_pendientes) == 1:
                    mensajes = [f"⏰ ¡Buenos días! No olvides completar tu hábito: {habitos_pendientes[0].nombre}"]
                else:
                    nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                    if len(habitos_pendientes) > 2:
                        nombres += f" y {len(habitos_pendientes) - 2} más"
                    mensajes = [f"⏰ ¡Buenos días! Tienes hábitos pendientes: {nombres}"]
            else:
                mensajes = ["🌟 ¡Excelente! Ya has completado todos tus hábitos. ¡Sigue así!"]
            titulo = "¡Recordatorio de Mañana! ⏰"
            
        elif 13 <= hora_actual <= 15:  # Mediodía (1-3 PM)
            tipo_notificacion = "recordatorio_mediodia"
            if habitos_pendientes:
                if len(habitos_pendientes) == 1:
                    mensajes = [f"⏰ ¡Mediodía! No olvides completar tu hábito: {habitos_pendientes[0].nombre}"]
                else:
                    nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                    if len(habitos_pendientes) > 2:
                        nombres += f" y {len(habitos_pendientes) - 2} más"
                    mensajes = [f"⏰ ¡Mediodía! Tienes hábitos pendientes: {nombres}"]
            else:
                mensajes = ["🚀 ¡Excelente! Todos tus hábitos están completados. ¡Sigue así!"]
            titulo = "¡Recordatorio de Mediodía! ⏰"
            
        elif 16 <= hora_actual <= 18:  # Tarde (4-6 PM)
            tipo_notificacion = "motivacion_tarde"
            if porcentaje_completado >= 80:
                mensajes = [
                    "🚀 ¡Increíble progreso! Has completado la mayoría de tus hábitos. ¡Sigue así!",
                    "💫 ¡Espectacular! Tu dedicación está dando frutos. ¡Eres una inspiración!",
                    "🌟 ¡Excelente trabajo! Has demostrado que puedes lograr lo que te propones."
                ]
            elif porcentaje_completado >= 50:
                mensajes = [
                    "💪 ¡Buen trabajo! Has completado más de la mitad de tus hábitos. ¡Continúa!",
                    "🌱 ¡Cada paso cuenta! Estás construyendo hábitos sólidos. ¡Sigue adelante!",
                    "✨ ¡Progreso notable! Cada hábito completado te acerca a tus metas."
                ]
            else:
                mensajes = [
                    "🌅 ¡Aún hay tiempo! La tarde es perfecta para completar tus hábitos pendientes.",
                    "💪 ¡Tú puedes! Cada hábito que completes hoy es una victoria.",
                    "🌟 ¡No te rindas! Cada pequeño paso te hace más fuerte."
                ]
            titulo = "¡Motivación de Tarde! 🌅"
            
        elif 19 <= hora_actual <= 21:  # Noche temprana (7-9 PM)
            tipo_notificacion = "recordatorio_noche"
            if habitos_pendientes:
                if len(habitos_pendientes) == 1:
                    mensajes = [f"🌙 ¡Última oportunidad! Completa tu hábito: {habitos_pendientes[0].nombre}"]
                else:
                    nombres = ", ".join([h.nombre for h in habitos_pendientes[:2]])
                    if len(habitos_pendientes) > 2:
                        nombres += f" y {len(habitos_pendientes) - 2} más"
                    mensajes = [f"🌙 ¡Última oportunidad! Completa tus hábitos: {nombres}"]
            else:
                mensajes = ["🎉 ¡Perfecto! Todos tus hábitos están completados. ¡Día exitoso!"]
            titulo = "¡Recordatorio Final! 🌙"
            
        elif 22 <= hora_actual <= 23 or 0 <= hora_actual <= 5:  # Noche tarde (10 PM - 5 AM)
            tipo_notificacion = "celebracion"
            if porcentaje_completado >= 90:
                mensajes = [
                    "🎉 ¡PERFECTO! ¡Has completado todos tus hábitos! ¡Eres increíble!",
                    "🏆 ¡CAMPEÓN! ¡Día perfecto! Has demostrado que puedes lograr todo lo que te propones!",
                    "⭐ ¡ESTRELLA! ¡Has brillado hoy! Todos tus hábitos completados. ¡Eres una inspiración!"
                ]
                titulo = "¡CELEBRACIÓN! 🎉"
            else:
                mensajes = [
                    "🌙 ¡Buenas noches! Mañana será otro día para mejorar. ¡Descansa bien!",
                    "✨ ¡Hasta mañana! Cada día es una nueva oportunidad para crecer.",
                    "🌟 ¡Buenas noches! Gracias por tu esfuerzo hoy. ¡Mañana será mejor!"
                ]
                titulo = "¡Buenas Noches! 🌙"
        else:
            # Hora no programada
            return JsonResponse({"status": "no_schedule", "message": "No hay notificaciones programadas para esta hora"})
        
        import random
        mensaje = random.choice(mensajes)
        
        print(f"Tipo de notificación: {tipo_notificacion}")
        print(f"Mensaje seleccionado: {mensaje}")
        print(f"Porcentaje completado: {porcentaje_completado}%")
        print(f"Hábitos completados: {habitos_completados}/{total_habitos}")
        print(f"=== FIN NOTIFICACIÓN AUTOMÁTICA ===")
        
        # Enviar notificación
        push_info = PushInformation.objects.filter(user=request.user).first()
        if push_info:
            try:
                payload = {
                    "head": titulo,
                    "body": mensaje,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación automática enviada: {mensaje}")
                return JsonResponse({
                    "status": "success", 
                    "message": mensaje,
                    "tipo": tipo_notificacion,
                    "hora": f"{hora_actual}:{now.minute}",
                    "porcentaje": porcentaje_completado,
                    "completados": habitos_completados,
                    "total": total_habitos
                })
                
            except Exception as e:
                print(f"Error enviando notificación automática: {str(e)}")
                # En desarrollo, simular envío exitoso
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    print("Simulando envío automático en desarrollo")
                    return JsonResponse({
                        "status": "success", 
                        "message": mensaje + " (simulado en desarrollo)",
                        "tipo": tipo_notificacion,
                        "hora": f"{hora_actual}:{now.minute}",
                        "porcentaje": porcentaje_completado,
                        "completados": habitos_completados,
                        "total": total_habitos
                    })
                else:
                    return JsonResponse({"status": "error", "message": f"Error enviando notificación: {str(e)}"})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push configurada"})
            
    except Exception as e:
        print(f"Error en notificación automática por horario: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})

@login_required
def notificacion_tareas_automatica(request):
    """Envía notificaciones automáticas para tareas según la hora del día"""
    try:
        from datetime import datetime
        now = timezone.localtime(timezone.now())
        hora_actual = now.hour
        today = now.date()
        
        print(f"=== NOTIFICACIÓN TAREAS AUTOMÁTICA ===")
        print(f"Hora actual: {hora_actual}:{now.minute}")
        print(f"Fecha: {today}")
        
        # Obtener tareas del usuario
        tareas = Actividad.objects.filter(user=request.user, tipo='tarea').order_by('-fecha_creacion')
        total_tareas = tareas.count()
        
        if total_tareas == 0:
            return JsonResponse({"status": "no_tasks", "message": "No tienes tareas configuradas"})
        
        # Obtener tareas recientes (últimas 5)
        tareas_recientes = tareas[:5]
        
        # Determinar tipo de notificación según la hora
        if 6 <= hora_actual <= 9:  # Mañana temprana (6-9 AM)
            tipo_notificacion = "tareas_manana"
            mensajes = [
                "📋 ¡Buenos días! Aquí tienes tus tareas del día:",
                "📝 ¡Hola! Estas son tus tareas para hoy:",
                "✅ ¡Buenos días! Revisa tus tareas pendientes:"
            ]
            titulo = "¡Tareas del Día! 📋"
            
        elif 10 <= hora_actual <= 12:  # Mañana media (10-12 AM)
            tipo_notificacion = "tareas_manana_media"
            mensajes = [
                "⏰ ¡Mediodía! No olvides revisar tus tareas:",
                "📋 ¡Buenos días! Aquí están tus tareas pendientes:",
                "✅ ¡Hola! Revisa el progreso de tus tareas:"
            ]
            titulo = "¡Recordatorio de Tareas! ⏰"
            
        elif 13 <= hora_actual <= 15:  # Mediodía (1-3 PM)
            tipo_notificacion = "tareas_mediodia"
            mensajes = [
                "⏰ ¡Mediodía! Revisa tus tareas pendientes:",
                "📋 ¡Hora de revisar! Estas son tus tareas:",
                "✅ ¡Mediodía! No olvides tus tareas:"
            ]
            titulo = "¡Tareas de Mediodía! ⏰"
            
        elif 16 <= hora_actual <= 18:  # Tarde (4-6 PM)
            tipo_notificacion = "tareas_tarde"
            mensajes = [
                "🌅 ¡Tarde! Revisa el progreso de tus tareas:",
                "📋 ¡Aún hay tiempo! Estas son tus tareas pendientes:",
                "✅ ¡Tarde! No olvides completar tus tareas:"
            ]
            titulo = "¡Tareas de Tarde! 🌅"
            
        elif 19 <= hora_actual <= 21:  # Noche temprana (7-9 PM)
            tipo_notificacion = "tareas_noche"
            mensajes = [
                "🌙 ¡Noche! Última oportunidad para revisar tus tareas:",
                "📋 ¡Final del día! Revisa tus tareas pendientes:",
                "✅ ¡Noche! No olvides tus tareas importantes:"
            ]
            titulo = "¡Tareas de Noche! 🌙"
            
        elif 22 <= hora_actual <= 23 or 0 <= hora_actual <= 5:  # Noche tarde (10 PM - 5 AM)
            tipo_notificacion = "tareas_resumen"
            mensajes = [
                "🌙 ¡Buenas noches! Resumen de tus tareas del día:",
                "�� ¡Hasta mañana! Aquí están tus tareas:",
                "✅ ¡Descansa! Revisa tus tareas completadas:"
            ]
            titulo = "¡Resumen de Tareas! 🌙"
        else:
            # Hora no programada
            return JsonResponse({"status": "no_schedule", "message": "No hay notificaciones de tareas programadas para esta hora"})
        
        import random
        mensaje_base = random.choice(mensajes)
        
        # Crear mensaje con descripción de tareas
        descripcion_tareas = []
        for i, tarea in enumerate(tareas_recientes, 1):
            descripcion = f"{i}. {tarea.nombre}"
            if tarea.descripcion and tarea.descripcion.strip():
                descripcion += f" - {tarea.descripcion}"
            descripcion_tareas.append(descripcion)
        
        mensaje_completo = f"{mensaje_base}\n\n" + "\n".join(descripcion_tareas)
        
        if total_tareas > 5:
            mensaje_completo += f"\n\n... y {total_tareas - 5} tareas más"
        
        print(f"Tipo de notificación: {tipo_notificacion}")
        print(f"Mensaje base: {mensaje_base}")
        print(f"Total tareas: {total_tareas}")
        print(f"Tareas mostradas: {len(tareas_recientes)}")
        print(f"=== FIN NOTIFICACIÓN TAREAS ===")
        
        # Enviar notificación
        push_info = PushInformation.objects.filter(user=request.user).first()
        if push_info:
            try:
                payload = {
                    "head": titulo,
                    "body": mensaje_completo,
                    "icon": "/static/images/SOULTRACK-ICON.png"
                }
                
                send_user_notification(
                    user=request.user, 
                    payload=json.dumps(payload), 
                    ttl=1000
                )
                
                print(f"Notificación de tareas enviada: {mensaje_base}")
                return JsonResponse({
                    "status": "success", 
                    "message": mensaje_completo,
                    "tipo": tipo_notificacion,
                    "hora": f"{hora_actual}:{now.minute}",
                    "total_tareas": total_tareas,
                    "tareas_mostradas": len(tareas_recientes)
                })
                
            except Exception as e:
                print(f"Error enviando notificación de tareas: {str(e)}")
                # En desarrollo, simular envío exitoso
                if 'development-simulation' in str(push_info.subscription.endpoint):
                    print("Simulando envío de tareas en desarrollo")
                    return JsonResponse({
                        "status": "success", 
                        "message": mensaje_completo + " (simulado en desarrollo)",
                        "tipo": tipo_notificacion,
                        "hora": f"{hora_actual}:{now.minute}",
                        "total_tareas": total_tareas,
                        "tareas_mostradas": len(tareas_recientes)
                    })
                else:
                    return JsonResponse({"status": "error", "message": f"Error enviando notificación: {str(e)}"})
        else:
            return JsonResponse({"status": "no_subscription", "message": "No tienes suscripción push configurada"})
            
    except Exception as e:
        print(f"Error en notificación automática de tareas: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)})
