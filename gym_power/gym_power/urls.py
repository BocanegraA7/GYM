"""
URL configuration for gym_power project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
 
 # Vistas propias del proyecto, app user
from user import views
from clases import views as class_views

urlpatterns = [
    #  Redirección según autenticación
    path('', lambda request: redirect('home') if request.user.is_authenticated else redirect('login')),
    
    path('admin/', admin.site.urls),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('editar/<int:user_id>/', views.editar_perfil, name='editar_usuario'),
    path('listar/', views.listar_usuarios, name='listar_usuarios'),
    path('eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('home/', views.home, name='home'),  
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    
    # Reportes
    path("reporte/pdf/", views.generar_pdf, name="generar_pdf"),
    path("reportes/", views.reportes_view, name="reportes"),
    path("reportes/pdf/", views.generar_pdf, name="export_pdf"),
    path("reportes/excel/", views.generar_excel, name="export_excel"),
    path("reportes/telegram/", views.enviar_reporte_telegram, name="send_report_telegram"),
    path("reportes/email/", views.enviar_reporte_email, name="send_report_email"),

    # notificacion
    # --- Notificaciones CRUD ---
    path("notificaciones/", views.notificaciones_view, name="notificaciones"),
    path("notificaciones/<int:notificacion_id>/", views.notificaciones_view, name="notificacion_edit"),
    path("notificaciones/delete/<int:id>/", views.notificacion_delete, name="notificacion_delete"),
    path("notificaciones/enviar/<int:id>/", views.notificacion_enviar, name="notificacion_enviar"),


    # 🏋️‍♂️ CRUD de clases (módulo gimnasio)
    path('clases/', class_views.listar_clases, name='listar_clases'),
    path('clases/crear/', class_views.crear_clase, name='crear_clase'),
    path('clases/editar/<int:clase_id>/', class_views.editar_clase, name='editar_clase'),
    path('clases/eliminar/<int:clase_id>/', class_views.eliminar_clase, name='eliminar_clase'),
    path('clases/inscribirse/<int:clase_id>/', class_views.inscribirse_clase, name='inscribirse_clase'),
    path('clases/ver/<int:clase_id>/', class_views.ver_clase, name='ver_clase'),

    
    # API
    path('api/v1/users/', views.UserListView.as_view()),
]
