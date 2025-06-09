from django.urls import path
from . import views

app_name = 'Users'
urlpatterns = [ 
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.signin, name='login'),
    path('logout/', views.signout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
