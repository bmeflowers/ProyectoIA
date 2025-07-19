from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Users.views import home, signin
from . import views
from django.urls import path

urlpatterns = [
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', signin, name='login'),
    path('users/', include('Users.urls', namespace='users')),
    path('activities/', include('activities.urls', namespace='activities')),
    path('data_analytics/', include('data_analytics.urls', namespace='data_analytics')),
    path('webpush/', include('webpush.urls')),
    path('reminders/', include('reminders.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)