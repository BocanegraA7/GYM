from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from .models import Clase
from user.models import Users
from .forms import ClaseForm

@login_required
def listar_clases(request):
    """Listar todas las clases"""
    clases = Clase.objects.all().order_by('fecha', 'hora')

    # Obtener rol del usuario
    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        role_name = None

    return render(request, "listar_clases.html", {
        "clases": clases,
        "role_name": role_name,
        "user": request.user
    })


@login_required
def ver_clase(request, clase_id):
    """Ver detalle de una clase"""
    clase = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        role_name = None

    return render(request, "ver_clase.html", {
        "clase": clase,
        "role_name": role_name,
        "user": request.user
    })


@login_required
def crear_clase(request):
    """Crear una clase"""
    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        role_name = None

    if request.method == "POST":
        form = ClaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase creada correctamente.")
            return redirect("listar_clases")
    else:
        form = ClaseForm()

    return render(request, "crear_clase.html", {
        "form": form,
        "role_name": role_name,
        "user": request.user
    })


@login_required
def editar_clase(request, clase_id):
    """Editar una clase existente"""
    clase = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        role_name = None

    if request.method == "POST":
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase actualizada correctamente.")
            return redirect("ver_clase", clase_id=clase.id)
    else:
        form = ClaseForm(instance=clase)

    return render(request, "editar_clase.html", {
        "form": form,
        "clase": clase,
        "role_name": role_name,
        "user": request.user
    })


@login_required
def eliminar_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    if request.method == "POST":
        clase.delete()
        messages.success(request,"¡Clase eliminada con éxito!")
    
    return redirect("listar_clases")


@login_required
def inscribirse_clase(request, clase_id):
    """Inscribirse a una clase"""
    clase = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        role_name = None

    if request.method == "POST":
        if clase.cupos > 0:
            clase.cupos -= 1
            clase.save()
            messages.success(request, "Te has inscrito correctamente.")
        else:
            messages.error(request, "No hay cupos disponibles.")

    return redirect("ver_clase", clase_id=clase.id)