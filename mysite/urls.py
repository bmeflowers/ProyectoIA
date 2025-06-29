from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from Users.views import home, signin  # Importaciones desde Users.views
from . import views  # Importación crucial que te faltaba

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # Ruta principal (home)
    path('dashboard/', views.dashboard, name='dashboard'),  # Ahora funcionará
    path('login/', signin, name='login'),  # Ruta para login
    path('users/', include('Users.urls', namespace='users')),
    path('activities/', include('activities.urls', namespace='activities')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)