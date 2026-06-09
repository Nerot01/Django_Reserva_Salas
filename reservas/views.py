from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Sala, Reserva
from .forms import ReservaForm, SalaForm, BLOQUES_HORARIOS, RegistroForm
from datetime import date, datetime

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
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('panel')
    else:
        form = RegistroForm()
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
        form = ReservaForm(request.POST, sala=sala)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.sala = sala
            reserva.usuario = request.user
            reserva.save()
            return redirect('panel')
    else:
        hoy = date.today().strftime('%Y-%m-%d')
        form = ReservaForm(sala=sala, initial={'fecha': hoy})
    
    return render(request, 'reservas/reservar.html', {
        'form': form,
        'sala': sala,
        'bloques': BLOQUES_HORARIOS
    })

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

# Decorador personalizado para requerir permisos de administrador
def admin_member_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden("No tienes permisos de administrador para realizar esta acción.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# CRUD de Salas para Administrador
@admin_member_required
def salas_admin_list(request):
    salas = Sala.objects.all()
    return render(request, 'reservas/salas_admin_list.html', {'salas': salas})

@admin_member_required
def sala_crear(request):
    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('salas_admin_list')
    else:
        form = SalaForm()
    return render(request, 'reservas/sala_form.html', {'form': form, 'titulo': 'Crear Nueva Sala'})

@admin_member_required
def sala_editar(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            return redirect('salas_admin_list')
    else:
        form = SalaForm(instance=sala)
    return render(request, 'reservas/sala_form.html', {'form': form, 'titulo': 'Editar Sala', 'sala': sala})

@admin_member_required
def sala_eliminar(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.method == 'POST':
        sala.delete()
    return redirect('salas_admin_list')

# API para consultar reservas ocupadas en una sala y fecha determinadas
@login_required
def reservas_ocupadas_api(request):
    sala_id = request.GET.get('sala_id')
    fecha_str = request.GET.get('fecha')
    excluir_reserva_id = request.GET.get('excluir_reserva_id')
    
    if not sala_id or not fecha_str:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Fecha inválida'}, status=400)
        
    reservas = Reserva.objects.filter(sala_id=sala_id, fecha=fecha)
    if excluir_reserva_id:
        try:
            reservas = reservas.exclude(id=int(excluir_reserva_id))
        except ValueError:
            pass
            
    # Comprobar traslapes para cada uno de los 20 bloques predefinidos
    ocupados = []
    for bloque_val, _ in BLOQUES_HORARIOS:
        inicio_str, fin_str = bloque_val.split('-')
        hora_inicio = datetime.strptime(inicio_str.strip(), '%H:%M').time()
        hora_fin = datetime.strptime(fin_str.strip(), '%H:%M').time()
        
        # Hay traslape si la reserva existente empieza antes del fin del bloque
        # Y termina después del inicio del bloque
        overlap = reservas.filter(
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        )
        if overlap.exists():
            ocupados.append(bloque_val)
        
    return JsonResponse({'ocupados': ocupados})

@login_required
def reserva_editar(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Comprobar permisos (propietario o admin)
    if not (request.user == reserva.usuario or request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("No tienes permiso para modificar esta reserva.")
        
    if request.method == 'POST':
        form = ReservaForm(request.POST, instance=reserva, sala=reserva.sala)
        if form.is_valid():
            form.save()
            return redirect('panel')
    else:
        # Reconstruir el valor del bloque para el formulario a partir de hora_inicio y hora_fin
        inicio_str = reserva.hora_inicio.strftime('%H:%M')
        fin_str = reserva.hora_fin.strftime('%H:%M')
        bloque_val = f"{inicio_str}-{fin_str}"
        
        form = ReservaForm(instance=reserva, sala=reserva.sala, initial={'bloque': bloque_val})
        
    return render(request, 'reservas/reservar.html', {
        'form': form,
        'sala': reserva.sala,
        'bloques': BLOQUES_HORARIOS,
        'es_edicion': True,
        'reserva': reserva
    })
