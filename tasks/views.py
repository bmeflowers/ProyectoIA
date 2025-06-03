from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.decorators import login_required



# Create your views here.
def home (request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html', {
            'form': CustomUserCreationForm()
        })
    else:
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': form,
                    'error': 'El nombre de usuario ya existe.'
                })
        else:
            return render(request, 'signup.html', {
                'form': form,
                'error': 'Verifica los datos ingresados.'
            })

def tasks (request):
    return render (request, 'task.html')

def signout(request):
    logout(request)
    return redirect('home')

def signin(request):
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': CustomAuthenticationForm()
        })
    else:
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Buscar por email si es necesario
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = username_or_email

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('tasks')
            else:
                return render(request, 'signin.html', {
                    'form': form,
                    'error': 'Usuario o contraseña incorrectos.'
                })
        else:
            return render(request, 'signin.html', {
                'form': form,
                'error': 'Datos inválidos.'
            })
        