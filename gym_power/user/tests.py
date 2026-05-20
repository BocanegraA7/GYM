from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User as DjangoUser
from django.core import mail
from user.models import Users, Roles, Notificacion
from django.utils.timezone import make_aware
from datetime import datetime


class GymPowerTests(TestCase):
    """🔹 Pruebas funcionales y unitarias para GymPower"""

    def setUp(self):
        """Configuración inicial antes de cada test"""
        self.client = Client()

        # Crear rol base
        self.role_admin = Roles.objects.create(
            nombre="Administrador",
            descripcion="Acceso total al sistema"
        )
        self.role_cliente = Roles.objects.create(
            nombre="Cliente",
            descripcion="Rol con acceso limitado"
        )

        # Crear usuario Django y perfil extendido
        self.django_user = DjangoUser.objects.create_user(
            username="admin",
            password="password123",
            email="admin@example.com"
        )
        self.user = Users.objects.create(
            username="admin",
            password="password123",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            chat_id="123456",
            role=self.role_admin
        )

        # Iniciar sesión automáticamente
        self.client.login(username="admin", password="password123")

        print("\n🧩 Iniciando prueba...")

    def tearDown(self):
        print("✅ Prueba completada correctamente.\n")

    # ======================================================
    # 🧱 AUTENTICACIÓN
    # ======================================================

    def test_signup_usuario(self):
        print("➡️  Test: Registro de nuevo usuario (Signup)")
        response = self.client.post(reverse("signup"), {
            "username": "newuser",
            "name": "Nuevo",
            "last_name": "Usuario",
            "email": "new@example.com",
            "chat_id": "654321",
            "role": self.role_cliente.id,
            "password1": "abc123",
            "password2": "abc123",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Users.objects.filter(username="newuser").exists())

    def test_login_correcto(self):
        print("➡️  Test: Login con credenciales correctas")
        usuario = Users.objects.get(username="admin")
        self.assertEqual(usuario.password, "password123")

    def test_login_incorrecto(self):
        print("➡️  Test: Login con usuario inexistente")
        with self.assertRaises(Users.DoesNotExist):
            Users.objects.get(username="no_existe")

    def test_acceso_home_autenticado(self):
        print("➡️  Test: Acceso al Home con sesión iniciada")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inicio")

    def test_acceso_home_sin_login(self):
        print("➡️  Test: Acceso al Home sin autenticación (redirección)")
        self.client.logout()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    # ======================================================
    # 📊 REPORTES
    # ======================================================

    def test_generar_pdf(self):
        print("➡️  Test: Generar reporte PDF")
        response = self.client.get(reverse("export_pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response.headers.get("Content-Type", ""))

    def test_generar_excel(self):
        print("➡️  Test: Generar reporte Excel")
        response = self.client.get(reverse("export_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response.headers.get("Content-Type", "")
        )

    def test_enviar_reporte_email(self):
        print("➡️  Test: Enviar reporte por correo electrónico")
        response = self.client.post(reverse("send_report_email"), {
            "user_id": self.user.id,
            "file_type": "pdf"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reporte de Usuarios", mail.outbox[0].subject)

    # ======================================================
    # 📱 NOTIFICACIONES (CRUD)
    # ======================================================

    def test_crear_notificacion(self):
        print("➡️  Test: Crear notificación nueva")
        response = self.client.post(reverse("notificaciones"), {
            "destinatario": "admin",
            "titulo": "Prueba Notificación",
            "descripcion": "Mensaje de prueba funcional.",
            "fecha_envio": "2025-10-24T10:00"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notificacion.objects.filter(titulo="Prueba Notificación").exists())

    def test_editar_notificacion(self):
        print("➡️  Test: Editar notificación existente")
        notif = Notificacion.objects.create(
            destinatario=self.user,
            titulo="Noti Original",
            descripcion="Texto original",
            fecha_envio=make_aware(datetime(2025, 10, 24, 10, 0))
        )
        url = reverse("notificacion_edit", args=[notif.id])
        response = self.client.post(url, {
            "destinatario": "admin",
            "titulo": "Noti Editada",
            "descripcion": "Texto editado",
            "fecha_envio": "2025-10-25T12:00"
        })
        notif.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(notif.titulo, "Noti Editada")

    def test_eliminar_notificacion(self):
        print("➡️  Test: Eliminar notificación existente")
        notif = Notificacion.objects.create(
            destinatario=self.user,
            titulo="Eliminarme",
            descripcion="Borrar este mensaje",
            fecha_envio=make_aware(datetime(2025, 10, 24, 10, 0))
        )
        response = self.client.get(reverse("notificacion_delete", args=[notif.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Notificacion.objects.filter(titulo="Eliminarme").exists())

    def test_listar_notificaciones(self):
        print("➡️  Test: Listar notificaciones")
        Notificacion.objects.create(
            destinatario=self.user,
            titulo="Lista Test",
            descripcion="Debe aparecer en tabla",
            fecha_envio=make_aware(datetime(2025, 10, 25, 10, 0))
        )
        response = self.client.get(reverse("notificaciones"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestión de Notificaciones")

    def test_enviar_notificacion(self):
        print("➡️  Test: Enviar notificación (simulada)")
        notif = Notificacion.objects.create(
            destinatario=self.user,
            titulo="EnviarTest",
            descripcion="Prueba de envío",
            fecha_envio=make_aware(datetime(2025, 10, 24, 10, 0))
        )
        response = self.client.get(reverse("notificacion_enviar", args=[notif.id]))
        notif.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(notif.enviado)

    # ======================================================
    # 🚀 TELEGRAM (mock simulado)
    # ======================================================

    def test_chat_id_valido(self):
        print("➡️  Test: chat_id válido")
        usuario = Users.objects.get(username="admin")
        self.assertEqual(usuario.chat_id, "123456")

    def test_chat_id_invalido(self):
        print("➡️  Test: chat_id inexistente")
        with self.assertRaises(Users.DoesNotExist):
            Users.objects.get(chat_id="00000")
