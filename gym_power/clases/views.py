from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Clase
from user.models import Users
from .forms import ClaseForm

@login_required
def listar_clases(request):
    """Listar todas las clases"""
    from django.utils import timezone
    from datetime import datetime
    from django.db.models import Q

    clases_qs = Clase.objects.all().order_by('fecha', 'hora')

    # Filtro de búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        clases_qs = clases_qs.filter(
            Q(nombre__icontains=q) |
            Q(entrenador__username__icontains=q) |
            Q(lugar__icontains=q)
        )

    # Obtener rol del usuario
    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        perfil = None
        role_name = None

    es_admin = (role_name == "Administrador")
    es_entrenador = (role_name == "Entrenador")
    es_cliente = (role_name == "Cliente")

    # Clases en las que está inscrito el cliente
    inscritas_ids = []
    if es_cliente:
        inscritas_ids = list(request.user.clases_inscritas.values_list('clase_id', flat=True))

    # Determinar si la clase ya pasó
    ahora = timezone.now()
    clases = []
    for c in clases_qs:
        combined = datetime.combine(c.fecha, c.hora)
        if timezone.is_aware(ahora):
            combined = timezone.make_aware(combined)
        c.es_pasada = combined < ahora
        c.inscrito = c.id in inscritas_ids
        clases.append(c)

    return render(request, "listar_clases.html", {
        "clases": clases,
        "role_name": role_name,
        "es_admin": es_admin,
        "es_entrenador": es_entrenador,
        "es_cliente": es_cliente,
        "user": request.user,
        "perfil": perfil
    })


@login_required
def ver_clase(request, clase_id):
    """Ver detalle de una clase"""
    clase = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        perfil = None
        role_name = None

    # Clases alternativas para reprogramación
    from django.utils import timezone
    from datetime import datetime
    ahora = timezone.now()
    
    # Validar si esta clase ya pasó
    combined = datetime.combine(clase.fecha, clase.hora)
    if timezone.is_aware(ahora):
        combined = timezone.make_aware(combined)
    clase.es_pasada = combined < ahora

    inscrito = request.user.clases_inscritas.filter(clase=clase).exists()

    clases_disponibles_repro = []
    if inscrito and not clase.es_pasada:
        clases_qs = Clase.objects.exclude(id=clase.id).order_by('fecha', 'hora')
        for c in clases_qs:
            combined_c = datetime.combine(c.fecha, c.hora)
            if timezone.is_aware(ahora):
                combined_c = timezone.make_aware(combined_c)
            # Que esté en el futuro, tenga cupos y no esté ya inscrito
            if combined_c >= ahora and c.cupos > 0 and not request.user.clases_inscritas.filter(clase=c).exists():
                clases_disponibles_repro.append(c)

    return render(request, "ver_clase.html", {
        "clase": clase,
        "role_name": role_name,
        "user": request.user,
        "perfil": perfil,
        "inscrito": inscrito,
        "clases_disponibles_repro": clases_disponibles_repro
    })


@login_required
def crear_clase(request):
    """Crear una clase"""
    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        perfil = None
        role_name = None

    if request.method == "POST":
        post_data = request.POST.copy()
        if role_name == "Entrenador":
            post_data['entrenador'] = request.user.id
            
        form = ClaseForm(post_data)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase creada correctamente.")
            return redirect("listar_clases")
    else:
        form = ClaseForm()
        if role_name == "Entrenador":
            form.fields['entrenador'].initial = request.user
            form.fields['entrenador'].widget.attrs['disabled'] = 'true'
            form.fields['entrenador'].required = False

    return render(request, "crear_clase.html", {
        "form": form,
        "role_name": role_name,
        "user": request.user,
        "perfil": perfil
    })


@login_required
def editar_clase(request, clase_id):
    """Editar una clase existente"""
    clase = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        perfil = None
        role_name = None

    if request.method == "POST":
        form = ClaseForm(request.POST, instance=clase)
        if form.is_valid():
            form.save()
            messages.success(request, "Clase actualizada correctamente.")
            return redirect("ver_clase", clase_id=clase.id)
    else:
        form = ClaseForm(instance=clase)
        if role_name == "Entrenador":
            form.fields['entrenador'].widget.attrs['disabled'] = 'true'
            form.fields['entrenador'].required = False

    return render(request, "editar_clase.html", {
        "form": form,
        "clase": clase,
        "role_name": role_name,
        "user": request.user,
        "perfil": perfil
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
    from django.db import transaction
    from django.utils import timezone
    from datetime import datetime
    from .models import Inscripcion
    from telegram_service import send_telegram_message

    clase = get_object_or_404(Clase, id=clase_id)

    # Validar que no haya pasado
    ahora = timezone.now()
    combined = datetime.combine(clase.fecha, clase.hora)
    if timezone.is_aware(ahora):
        combined = timezone.make_aware(combined)
    if combined < ahora:
        messages.error(request, "No puedes inscribirte a una clase del pasado.")
        return redirect("ver_clase", clase_id=clase.id)

    try:
        perfil = Users.objects.get(username=request.user.username)
    except Users.DoesNotExist:
        perfil = None

    if request.method == "POST":
        # Evitar doble inscripción
        if Inscripcion.objects.filter(cliente=request.user, clase=clase).exists():
            messages.warning(request, "Ya estás inscrito en esta clase.")
            return redirect("ver_clase", clase_id=clase.id)

        if clase.cupos > 0:
            try:
                with transaction.atomic():
                    # Crear inscripción
                    Inscripcion.objects.create(cliente=request.user, clase=clase)
                    # Decrementar cupos
                    clase.cupos -= 1
                    clase.save()
                
                messages.success(request, "Te has inscrito correctamente.")

                # Notificación de Telegram
                if perfil and perfil.chat_id:
                    try:
                        mensaje = (
                            f"✅ <b>Inscripción Confirmada</b>\n\n"
                            f"🏋️‍♂️ Clase: <b>{clase.nombre}</b>\n"
                            f"📅 Fecha: {clase.fecha.strftime('%d/%m/%Y')}\n"
                            f"🕒 Hora: {clase.hora.strftime('%H:%M')}\n"
                            f"📍 Lugar: {clase.lugar}\n\n"
                            f"¡Prepárate para dar el 100%! 💪⚡"
                        )
                        send_telegram_message(perfil.chat_id, mensaje)
                    except Exception:
                        pass
            except Exception as e:
                messages.error(request, f"Error al procesar la inscripción: {str(e)}")
        else:
            messages.error(request, "No hay cupos disponibles.")

    referer = request.META.get('HTTP_REFERER', '')
    if 'calendario' in referer:
        return redirect('calendario_cliente')
    return redirect("ver_clase", clase_id=clase.id)


@login_required
def cancelar_inscripcion(request, clase_id):
    """Cancelar inscripción a una clase"""
    from django.db import transaction
    from django.utils import timezone
    from datetime import datetime
    from .models import Inscripcion
    from telegram_service import send_telegram_message

    clase = get_object_or_404(Clase, id=clase_id)

    # Validar que no haya pasado
    ahora = timezone.now()
    combined = datetime.combine(clase.fecha, clase.hora)
    if timezone.is_aware(ahora):
        combined = timezone.make_aware(combined)
    if combined < ahora:
        messages.error(request, "No puedes cancelar tu inscripción de una clase que ya ha finalizado.")
        return redirect("listar_clases")

    try:
        perfil = Users.objects.get(username=request.user.username)
    except Users.DoesNotExist:
        perfil = None

    inscripcion = Inscripcion.objects.filter(cliente=request.user, clase=clase).first()
    if not inscripcion:
        messages.error(request, "No estás inscrito en esta clase.")
        return redirect("listar_clases")

    if request.method == "POST":
        try:
            with transaction.atomic():
                inscripcion.delete()
                clase.cupos += 1
                clase.save()
            
            messages.success(request, "Has cancelado tu inscripción correctamente.")

            # Notificación de Telegram
            if perfil and perfil.chat_id:
                try:
                    mensaje = (
                        f"🗑️ <b>Inscripción Cancelada</b>\n\n"
                        f"Te has dado de baja de la clase:\n"
                        f"🏋️‍♂️ Clase: <b>{clase.nombre}</b>\n"
                        f"📅 Fecha: {clase.fecha.strftime('%d/%m/%Y')}\n"
                        f"🕒 Hora: {clase.hora.strftime('%H:%M')}\n\n"
                        f"Esperamos verte en otro entrenamiento. ¡No pierdas el impulso! 🔥"
                    )
                    send_telegram_message(perfil.chat_id, mensaje)
                except Exception:
                    pass
        except Exception as e:
            messages.error(request, f"Error al cancelar la inscripción: {str(e)}")

    referer = request.META.get('HTTP_REFERER', '')
    if 'calendario' in referer:
        return redirect('calendario_cliente')
    return redirect("listar_clases")


@login_required
def reprogramar_inscripcion(request, clase_id):
    """Reprogramar la inscripción de una clase a otra clase existente"""
    from django.db import transaction
    from django.utils import timezone
    from datetime import datetime
    from .models import Inscripcion
    from telegram_service import send_telegram_message

    clase_antigua = get_object_or_404(Clase, id=clase_id)

    try:
        perfil = Users.objects.get(username=request.user.username)
    except Users.DoesNotExist:
        perfil = None

    inscripcion = Inscripcion.objects.filter(cliente=request.user, clase=clase_antigua).first()
    if not inscripcion:
        messages.error(request, "No tienes una inscripción activa para esta clase.")
        return redirect("listar_clases")

    if request.method == "POST":
        nueva_clase_id = request.POST.get("nueva_clase_id")
        if not nueva_clase_id:
            messages.error(request, "No se seleccionó una nueva clase para reprogramar.")
            return redirect("listar_clases")

        clase_nueva = get_object_or_404(Clase, id=nueva_clase_id)

        # Validaciones de fechas pasadas
        ahora = timezone.now()
        
        # Clase antigua
        combined_antigua = datetime.combine(clase_antigua.fecha, clase_antigua.hora)
        if timezone.is_aware(ahora):
            combined_antigua = timezone.make_aware(combined_antigua)
        if combined_antigua < ahora:
            messages.error(request, "No puedes reprogramar una clase del pasado.")
            return redirect("listar_clases")

        # Clase nueva
        combined_nueva = datetime.combine(clase_nueva.fecha, clase_nueva.hora)
        if timezone.is_aware(ahora):
            combined_nueva = timezone.make_aware(combined_nueva)
        if combined_nueva < ahora:
            messages.error(request, "No puedes reprogramar a una clase que ya finalizó.")
            return redirect("listar_clases")

        if clase_nueva.cupos <= 0:
            messages.error(request, "La clase de destino no tiene cupos disponibles.")
            return redirect("listar_clases")

        if Inscripcion.objects.filter(cliente=request.user, clase=clase_nueva).exists():
            messages.warning(request, "Ya estás inscrito en la clase de destino.")
            return redirect("listar_clases")

        try:
            with transaction.atomic():
                # Borrar inscripción antigua y reponer cupo
                inscripcion.delete()
                clase_antigua.cupos += 1
                clase_antigua.save()

                # Crear inscripción nueva y descontar cupo
                Inscripcion.objects.create(cliente=request.user, clase=clase_nueva)
                clase_nueva.cupos -= 1
                clase_nueva.save()

            messages.success(request, f"¡Clase reprogramada con éxito a {clase_nueva.nombre}!")

            # Notificación de Telegram
            if perfil and perfil.chat_id:
                try:
                    mensaje = (
                        f"🔄 <b>Clase Reprogramada</b>\n\n"
                        f"Has modificado tu agenda deportiva:\n\n"
                        f"❌ <b>Clase Anterior:</b> {clase_antigua.nombre}\n"
                        f"📅 Fecha: {clase_antigua.fecha.strftime('%d/%m/%Y')} {clase_antigua.hora.strftime('%H:%M')}\n\n"
                        f"✅ <b>Nueva Clase:</b> {clase_nueva.nombre}\n"
                        f"📅 Fecha: {clase_nueva.fecha.strftime('%d/%m/%Y')} {clase_nueva.hora.strftime('%H:%M')}\n"
                        f"📍 Lugar: {clase_nueva.lugar}\n\n"
                        f"¡Listo para entrenar! 💪🏼🔥"
                    )
                    send_telegram_message(perfil.chat_id, mensaje)
                except Exception:
                    pass
        except Exception as e:
            messages.error(request, f"Error durante la reprogramación: {str(e)}")

    referer = request.META.get('HTTP_REFERER', '')
    if 'calendario' in referer:
        return redirect('calendario_cliente')
    return redirect("listar_clases")


@login_required
def calendario_cliente(request):
    """Renderiza el calendario de clases para el cliente"""
    import json
    from django.utils import timezone
    from datetime import datetime
    from .models import Inscripcion

    try:
        perfil = Users.objects.get(username=request.user.username)
        role_name = perfil.role.nombre if perfil.role else None
    except Users.DoesNotExist:
        perfil = None
        role_name = None

    if role_name != "Cliente" and role_name != "Administrador":
        return redirect("home")

    clases_qs = Clase.objects.all().order_by('fecha', 'hora')
    inscritas_ids = list(request.user.clases_inscritas.values_list('clase_id', flat=True))

    ahora = timezone.now()
    clases_data = []

    for c in clases_qs:
        combined = datetime.combine(c.fecha, c.hora)
        if timezone.is_aware(ahora):
            combined = timezone.make_aware(combined)
        
        es_pasada = combined < ahora
        inscrito = c.id in inscritas_ids

        # Formato de evento para FullCalendar
        clases_data.append({
            "id": c.id,
            "title": c.nombre,
            "start": f"{c.fecha.isoformat()}T{c.hora.isoformat()}",
            "description": c.descripcion,
            "entrenador": c.entrenador.username,
            "lugar": c.lugar,
            "cupos": c.cupos,
            "es_pasada": es_pasada,
            "inscrito": inscrito,
            "duracion": c.duracion_min
        })

    # Filtrar clases alternativas disponibles para reprogramación
    clases_disponibles_repro = []
    for c in clases_qs:
        combined = datetime.combine(c.fecha, c.hora)
        if timezone.is_aware(ahora):
            combined = timezone.make_aware(combined)
        if combined >= ahora and c.cupos > 0 and c.id not in inscritas_ids:
            clases_disponibles_repro.append(c)

    return render(request, "calendario_cliente.html", {
        "clases_json": json.dumps(clases_data),
        "clases_disponibles_repro": clases_disponibles_repro,
        "role_name": role_name,
        "user": request.user,
        "perfil": perfil
    })