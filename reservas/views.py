from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'reservas/home.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('panel')
    else:
        form = AuthenticationForm()
    return render(request, 'reservas/login.html', {'form': form})

def registro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('panel')
    else:
        form = UserCreationForm()
    return render(request, 'reservas/registro.html', {'form': form})

@login_required
def panel(request):
    return render(request, 'reservas/panel.html')
