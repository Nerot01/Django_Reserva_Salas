from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('panel/', views.panel, name='panel'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
]
