from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, time
from .models import Sala, Reserva
from .forms import ReservaForm

class ReservaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.sala = Sala.objects.create(nombre='Sala de Prueba', capacidad=10, descripcion='Sala para pruebas unitarias')

    def test_sala_creation(self):
        """Verifica que la sala se cree y se guarde correctamente."""
        self.assertEqual(Sala.objects.count(), 1)
        self.assertEqual(self.sala.nombre, 'Sala de Prueba')

    def test_valid_reserva_creation(self):
        """Verifica que una reserva válida pueda crearse usando el formulario."""
        form_data = {
            'fecha': date.today(),
            'bloque': '08:10-08:50'
        }
        form = ReservaForm(data=form_data, sala=self.sala)
        self.assertTrue(form.is_valid(), form.errors)
        reserva = form.save(commit=False)
        reserva.sala = self.sala
        reserva.usuario = self.user
        reserva.save()

        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(reserva.hora_inicio, time(8, 10))
        self.assertEqual(reserva.hora_fin, time(8, 50))

    def test_duplicate_reserva_prevention(self):
        """Verifica que reservar el mismo bloque para la misma fecha y sala falle la validación."""
        # Crear la primera reserva
        Reserva.objects.create(
            sala=self.sala,
            usuario=self.user,
            fecha=date.today(),
            hora_inicio=time(8, 10),
            hora_fin=time(8, 50)
        )

        # Intentar reservar el mismo bloque
        form_data = {
            'fecha': date.today(),
            'bloque': '08:10-08:50'
        }
        form = ReservaForm(data=form_data, sala=self.sala)
        self.assertFalse(form.is_valid())
        self.assertIn('bloque', form.errors)
        self.assertEqual(
            form.errors['bloque'][0],
            "La sala ya se encuentra reservada para este bloque horario y fecha."
        )

    def test_past_date_reserva_prevention(self):
        """Verifica que reservar para una fecha pasada falle la validación."""
        past_date = date(2000, 1, 1)
        form_data = {
            'fecha': past_date,
            'bloque': '08:10-08:50'
        }
        form = ReservaForm(data=form_data, sala=self.sala)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha', form.errors)
        self.assertEqual(
            form.errors['fecha'][0],
            "No se pueden realizar reservas para fechas pasadas."
        )

    def test_reserva_editar_permission_denied(self):
        """Verifica que un usuario no pueda editar la reserva de otro usuario."""
        reserva = Reserva.objects.create(
            sala=self.sala,
            usuario=self.user,
            fecha=date.today(),
            hora_inicio=time(8, 10),
            hora_fin=time(8, 50)
        )
        
        otro_usuario = User.objects.create_user(username='otheruser', password='password123')
        self.client.login(username='otheruser', password='password123')
        
        response = self.client.get(f'/reserva/editar/{reserva.id}/')
        self.assertEqual(response.status_code, 403)

    def test_reserva_editar_success(self):
        """Verifica que el propietario de la reserva pueda editarla con éxito."""
        reserva = Reserva.objects.create(
            sala=self.sala,
            usuario=self.user,
            fecha=date.today(),
            hora_inicio=time(8, 10),
            hora_fin=time(8, 50)
        )
        
        self.client.login(username='testuser', password='password123')
        
        # Primero probamos el GET para asegurar que se carga el formulario con el bloque correcto
        response = self.client.get(f'/reserva/editar/{reserva.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '08:10 - 08:50')
        
        # Luego hacemos POST para cambiar la hora al segundo bloque (08:50-09:30)
        post_data = {
            'fecha': date.today().strftime('%Y-%m-%d'),
            'bloque': '08:50-09:30'
        }
        response = self.client.post(f'/reserva/editar/{reserva.id}/', data=post_data)
        self.assertRedirects(response, '/panel/')
        
        # Verificar en base de datos
        reserva.refresh_from_db()
        self.assertEqual(reserva.hora_inicio, time(8, 50))
        self.assertEqual(reserva.hora_fin, time(9, 30))

    def test_reserva_editar_admin_success(self):
        """Verifica que un administrador pueda editar cualquier reserva."""
        reserva = Reserva.objects.create(
            sala=self.sala,
            usuario=self.user,
            fecha=date.today(),
            hora_inicio=time(8, 10),
            hora_fin=time(8, 50)
        )
        
        admin_user = User.objects.create_superuser(username='adminuser', password='adminpassword')
        self.client.login(username='adminuser', password='adminpassword')
        
        post_data = {
            'fecha': date.today().strftime('%Y-%m-%d'),
            'bloque': '09:40-10:20'
        }
        response = self.client.post(f'/reserva/editar/{reserva.id}/', data=post_data)
        self.assertRedirects(response, '/panel/')
        
        # Verificar en base de datos
        reserva.refresh_from_db()
        self.assertEqual(reserva.hora_inicio, time(9, 40))
        self.assertEqual(reserva.hora_fin, time(10, 20))
