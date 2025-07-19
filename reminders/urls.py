# en reminders/urls.py o donde declares tus URLs
from django.urls import path
from .views import save_subscription

urlpatterns = [
    path('save-subscription/', save_subscription, name='save_subscription'),
]
