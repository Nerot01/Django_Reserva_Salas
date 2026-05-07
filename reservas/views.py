from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Página de Inicio de Reservas")

def login_view(request):
    return HttpResponse("Página de Login")

def registro_view(request):
    return HttpResponse("Página de Registro")
