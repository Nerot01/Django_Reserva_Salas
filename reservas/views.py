from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Sala, Reserva
from .forms import ReservaForm
from datetime import date

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
    salas = Sala.objects.prefetch_related('reservas', 'reservas__usuario').all()
    hoy = date.today()
    
    if request.user.is_superuser or request.user.is_staff:
        mis_reservas = Reserva.objects.all()
    else:
        mis_reservas = Reserva.objects.filter(usuario=request.user)
        
    context = {
        'salas': salas,
        'mis_reservas': mis_reservas,
        'hoy': hoy
    }
    return render(request, 'reservas/panel.html', context)

@login_required
def reservar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.sala = sala
            reserva.usuario = request.user
            reserva.save()
            return redirect('panel')
    else:
        form = ReservaForm()
    
    return render(request, 'reservas/reservar.html', {'form': form, 'sala': sala})

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Comprobar permisos (propietario o admin)
    if request.user == reserva.usuario or request.user.is_superuser or request.user.is_staff:
        if request.method == 'POST':
            reserva.delete()
    else:
        return HttpResponseForbidden("No tienes permiso para cancelar esta reserva.")
        
    return redirect('panel')
