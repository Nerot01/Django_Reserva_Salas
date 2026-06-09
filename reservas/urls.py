from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('panel/', views.panel, name='panel'),
    path('reservar/<int:sala_id>/', views.reservar_sala, name='reservar_sala'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('reserva/editar/<int:reserva_id>/', views.reserva_editar, name='reserva_editar'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    
    # Rutas para el CRUD de salas (admin)
    path('salas/', views.salas_admin_list, name='salas_admin_list'),
    path('salas/crear/', views.sala_crear, name='sala_crear'),
    path('salas/editar/<int:sala_id>/', views.sala_editar, name='sala_editar'),
    path('salas/eliminar/<int:sala_id>/', views.sala_eliminar, name='sala_eliminar'),
    
    # API para chequear bloques horarios ocupados
    path('api/reservas-ocupadas/', views.reservas_ocupadas_api, name='reservas_ocupadas_api'),
]

