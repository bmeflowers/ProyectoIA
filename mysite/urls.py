from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Users.views import home, signin
from . import views
from django.urls import path
from main.views import service_worker

urlpatterns = [
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', signin, name='login'),
    path('users/', include('Users.urls', namespace='users')),
    path('activities/', include('activities.urls', namespace='activities')),
    path('data_analytics/', include('data_analytics.urls', namespace='data_analytics')),
    path('webpush/', include(('webpush.urls', 'webpush'), namespace='webpush')),
    path('reminders/', include('reminders.urls')),
    path('service-worker.js', service_worker, name='service_worker'),
    path('test-push-status/', views.test_push_status, name='test_push_status'),
    path('test-vapid-keys/', views.test_vapid_keys, name='test_vapid_keys'),
    path('test-simple/', views.test_simple, name='test_simple'),
    path('clear-development-subscription/', views.clear_development_subscription, name='clear_development_subscription'),
    path('save-push-subscription/', views.save_push_subscription, name='save_push_subscription'),
    path('enviar-notificacion-inteligente/', views.enviar_notificacion_inteligente, name='enviar_notificacion_inteligente'),
    path('obtener-estado-habitos/', views.obtener_estado_habitos, name='obtener_estado_habitos'),
    path('enviar-notificacion-motivacional/', views.enviar_notificacion_motivacional_manual, name='enviar_notificacion_motivacional'),
    path('push-testing/', views.push_testing, name='push_testing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)