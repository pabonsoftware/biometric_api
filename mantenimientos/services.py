"""
Capa de servicios para mantenimientos de equipos biomédicos.

Implementa la lógica de negocio para operaciones CRUD, validaciones
y notificaciones relacionadas con mantenimientos.
"""

from django.db.models import QuerySet
from datetime import datetime

from .models import (
    Mantenimiento,
    OrdenServicio,
    ProgramacionMantenimiento,
)
from equipos.models import EquipoBiomedico
from usuarios.models import Usuario

from .exceptions import (
    MantenimientoNotFound,
    EquipoNotFound,
    ResponsableNotFound,
    EstadoInvalido,
    FechasInvalidas,
    DiagnosticoVacio,
    OrdenServicioNotFound,
    ProgramacionNotFound,
)

from notificaciones.models import Notificacion
from services.notifications.notificacion_service import notificar


# ============================================================================
# Servicios CRUD: Mantenimiento
# ============================================================================

def crear_mantenimiento(
    equipo_id=None,
    diagnostico=None,
    fecha_inicio=None,
    responsable_id=None,
    tipo='preventivo',
    fecha_fin=None,
    **kwargs
) -> Mantenimiento:
    """
    Crear un nuevo registro de mantenimiento para un equipo.

    Valida que el equipo exista, el diagnóstico no esté vacío, el responsable
    exista y las fechas sean consistentes.

    Puede recibir parámetros nombrados o un diccionario (de serializers).

    Args:
        equipo_id (int): ID del equipo biomédico a mantener.
        diagnostico (str): Descripción del diagnóstico del mantenimiento.
        fecha_inicio (datetime): Fecha y hora de inicio del mantenimiento.
        responsable_id (int): ID del usuario responsable del mantenimiento.
        tipo (str): Tipo de mantenimiento (default: 'preventivo').
        fecha_fin (datetime, optional): Fecha y hora de finalización.

    Returns:
        Mantenimiento: Instancia del mantenimiento creado.

    Raises:
        EquipoNotFound: Si el equipo no existe.
        ResponsableNotFound: Si el responsable no existe.
        DiagnosticoVacio: Si el diagnóstico está vacío.
        FechasInvalidas: Si fecha_fin < fecha_inicio.
    """
    # Extraer valores de kwargs para compatibilidad con serializers
    if isinstance(equipo_id, dict):
        datos = equipo_id
        equipo_id = datos.get('equipo_id') or datos.get('equipo').id
        diagnostico = datos.get('diagnostico')
        fecha_inicio = datos.get('fecha_inicio')
        responsable_id = datos.get('responsable_id') or datos.get('responsable').id
        tipo = datos.get('tipo', 'preventivo')
        fecha_fin = datos.get('fecha_fin')

    # Validar equipo
    try:
        equipo = EquipoBiomedico.objects.get(id=equipo_id)
    except EquipoBiomedico.DoesNotExist:
        raise EquipoNotFound(equipo_id)

    # Validar responsable
    try:
        responsable = Usuario.objects.get(id=responsable_id)
    except Usuario.DoesNotExist:
        raise ResponsableNotFound(responsable_id)

    # Validar diagnóstico
    if not diagnostico or not diagnostico.strip():
        raise DiagnosticoVacio()

    # Validar fechas
    if fecha_fin and fecha_inicio and fecha_fin < fecha_inicio:
        raise FechasInvalidas(fecha_inicio, fecha_fin)

    # Crear mantenimiento
    mantenimiento = Mantenimiento.objects.create(
        equipo=equipo,
        diagnostico=diagnostico.strip(),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        responsable=responsable,
        tipo=tipo,
        estado='pendiente'
    )

    # Enviar notificación
    mensaje = (
        f"Se ha creado un mantenimiento para el equipo {mantenimiento.equipo.nombre}"
    )
    destinatario = mantenimiento.responsable.correo

    if not _notificacion_existente(mensaje, destinatario):
        _crear_notificacion(mensaje, destinatario)
        _enviar_correo(destinatario, mensaje)

    return mantenimiento


def editar_mantenimiento(
    mantenimiento_id: int,
    datos: dict
) -> Mantenimiento:
    """
    Editar un mantenimiento existente.

    Valida campos actualizables y mantiene integridad de datos.
    Campos permitidos: diagnostico, fecha_inicio, fecha_fin, responsable_id,
    tipo, aprobado_por_id.

    Args:
        mantenimiento_id (int): ID del mantenimiento a editar.
        datos (dict): Diccionario con campos a actualizar.

    Returns:
        Mantenimiento: Instancia actualizada del mantenimiento.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
        ResponsableNotFound: Si se proporciona responsable_id inválido.
        DiagnosticoVacio: Si el diagnóstico se intenta establecer como vacío.
        FechasInvalidas: Si las fechas son inconsistentes.
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        raise MantenimientoNotFound(mantenimiento_id)

    # Campos permitidos
    campos_permitidos = {
        'diagnostico', 'fecha_inicio', 'fecha_fin', 'responsable_id',
        'tipo', 'aprobado_por_id'
    }

    # Validar y actualizar cada campo
    for clave, valor in datos.items():
        if clave not in campos_permitidos:
            continue

        if clave == 'diagnostico':
            if valor is not None:  # Permite actualizar
                if not valor.strip():
                    raise DiagnosticoVacio()
                setattr(mantenimiento, clave, valor.strip())

        elif clave == 'responsable_id':
            try:
                Usuario.objects.get(id=valor)
                setattr(mantenimiento, clave, valor)
            except Usuario.DoesNotExist:
                raise ResponsableNotFound(valor)

        elif clave == 'aprobado_por_id':
            if valor:
                try:
                    Usuario.objects.get(id=valor)
                    setattr(mantenimiento, clave, valor)
                except Usuario.DoesNotExist:
                    raise ResponsableNotFound(valor)
            else:
                setattr(mantenimiento, clave, None)

        else:
            setattr(mantenimiento, clave, valor)

    # Validar fechas después de actualizar
    if mantenimiento.fecha_fin and mantenimiento.fecha_inicio:
        if mantenimiento.fecha_fin < mantenimiento.fecha_inicio:
            raise FechasInvalidas(mantenimiento.fecha_inicio, mantenimiento.fecha_fin)

    mantenimiento.save()

    # Notificar actualización
    mensaje = (
        f"El mantenimiento para el equipo {mantenimiento.equipo.nombre} "
        f"ha sido actualizado."
    )
    destinatario = mantenimiento.responsable.correo

    if not _notificacion_existente(mensaje, destinatario):
        _crear_notificacion(mensaje, destinatario)
        _enviar_correo(destinatario, mensaje)

    return mantenimiento


def cambiar_estado(mantenimiento_id: int, nuevo_estado: str) -> Mantenimiento:
    """
    Cambiar el estado de un mantenimiento.

    Valida que el nuevo estado sea válido según ESTADO_CHOICES.

    Args:
        mantenimiento_id (int): ID del mantenimiento.
        nuevo_estado (str): Nuevo estado (pendiente, en_proceso, completado,
                           aprobado, supervisado, ejecutado).

    Returns:
        Mantenimiento: Instancia con estado actualizado.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
        EstadoInvalido: Si el nuevo estado no es válido.
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        raise MantenimientoNotFound(mantenimiento_id)

    # Validar estado
    estados_validos = [choice[0] for choice in Mantenimiento.ESTADO_CHOICES]
    if nuevo_estado not in estados_validos:
        raise EstadoInvalido(nuevo_estado)

    mantenimiento.estado = nuevo_estado
    mantenimiento.save()

    # Notificar cambio de estado
    mensaje = (
        f"El estado del mantenimiento para {mantenimiento.equipo.nombre} "
        f"ha cambiado a: {mantenimiento.get_estado_display()}"
    )
    destinatario = mantenimiento.responsable.correo

    if not _notificacion_existente(mensaje, destinatario):
        _crear_notificacion(mensaje, destinatario)
        _enviar_correo(destinatario, mensaje)

    return mantenimiento


def obtener_mantenimiento(mantenimiento_id: int) -> Mantenimiento:
    """
    Obtener un mantenimiento por su ID.

    Args:
        mantenimiento_id (int): ID del mantenimiento.

    Returns:
        Mantenimiento: Instancia del mantenimiento.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
    """
    try:
        return Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        raise MantenimientoNotFound(mantenimiento_id)


def listar_mantenimientos() -> QuerySet:
    """
    Listar todos los mantenimientos ordenados por fecha de creación.

    Returns:
        QuerySet: QuerySet con todos los mantenimientos.
    """
    return Mantenimiento.objects.all().order_by('-created_at')


def listar_por_equipo(equipo_id: int) -> QuerySet:
    """
    Listar mantenimientos filtrados por equipo.

    Args:
        equipo_id (int): ID del equipo biomédico.

    Returns:
        QuerySet: Mantenimientos del equipo especificado.

    Raises:
        EquipoNotFound: Si el equipo no existe.
    """
    try:
        equipo = EquipoBiomedico.objects.get(id=equipo_id)
    except EquipoBiomedico.DoesNotExist:
        raise EquipoNotFound(equipo_id)

    return Mantenimiento.objects.filter(equipo=equipo).order_by('-created_at')


def listar_por_responsable(responsable_id: int) -> QuerySet:
    """
    Listar mantenimientos asignados a un responsable específico.

    Args:
        responsable_id (int): ID del usuario responsable.

    Returns:
        QuerySet: Mantenimientos asignados al responsable.

    Raises:
        ResponsableNotFound: Si el responsable no existe.
    """
    try:
        Usuario.objects.get(id=responsable_id)
    except Usuario.DoesNotExist:
        raise ResponsableNotFound(responsable_id)

    return Mantenimiento.objects.filter(
        responsable_id=responsable_id
    ).order_by('-created_at')


def listar_por_estado(estado: str) -> QuerySet:
    """
    Listar mantenimientos filtrados por estado.

    Args:
        estado (str): Estado a filtrar (pendiente, en_proceso, completado,
                     aprobado, supervisado, ejecutado).

    Returns:
        QuerySet: Mantenimientos con el estado especificado.

    Raises:
        EstadoInvalido: Si el estado no es válido.
    """
    estados_validos = [choice[0] for choice in Mantenimiento.ESTADO_CHOICES]
    if estado not in estados_validos:
        raise EstadoInvalido(estado)

    return Mantenimiento.objects.filter(estado=estado).order_by('-created_at')


# ============================================================================
# Servicios CRUD: Orden de Servicio
# ============================================================================

def crear_orden_servicio(
    mantenimiento_id: int,
    tipo_servicio: str,
    descripcion: str,
    estado: str = 'pendiente'
) -> OrdenServicio:
    """
    Crear una nueva orden de servicio asociada a un mantenimiento.

    Args:
        mantenimiento_id (int): ID del mantenimiento.
        tipo_servicio (str): Tipo de servicio a realizar.
        descripcion (str): Descripción de la orden.
        estado (str): Estado inicial (default: 'pendiente').

    Returns:
        OrdenServicio: Instancia de la orden creada.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
    """
    try:
        mantenimiento = Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        raise MantenimientoNotFound(mantenimiento_id)

    orden = OrdenServicio.objects.create(
        mantenimiento=mantenimiento,
        tipo_servicio=tipo_servicio,
        descripcion=descripcion,
        estado=estado
    )

    # Notificar creación de orden
    mensaje = (
        f"Se ha creado una nueva orden de servicio para el equipo "
        f"{orden.mantenimiento.equipo.nombre}."
    )
    destinatario = orden.mantenimiento.responsable.correo

    if not _notificacion_existente(mensaje, destinatario):
        _crear_notificacion(mensaje, destinatario)
        _enviar_correo(destinatario, mensaje)

    return orden


def obtener_orden_servicio(orden_id: int) -> OrdenServicio:
    """
    Obtener una orden de servicio por su ID.

    Args:
        orden_id (int): ID de la orden.

    Returns:
        OrdenServicio: Instancia de la orden.

    Raises:
        OrdenServicioNotFound: Si la orden no existe.
    """
    try:
        return OrdenServicio.objects.get(id=orden_id)
    except OrdenServicio.DoesNotExist:
        raise OrdenServicioNotFound(orden_id)


def listar_ordenes_por_mantenimiento(mantenimiento_id: int) -> QuerySet:
    """
    Listar órdenes de servicio de un mantenimiento específico.

    Args:
        mantenimiento_id (int): ID del mantenimiento.

    Returns:
        QuerySet: Órdenes de servicio del mantenimiento.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
    """
    try:
        Mantenimiento.objects.get(id=mantenimiento_id)
    except Mantenimiento.DoesNotExist:
        raise MantenimientoNotFound(mantenimiento_id)

    return OrdenServicio.objects.filter(
        mantenimiento_id=mantenimiento_id
    ).order_by('-created_at')


# ============================================================================
# Servicios CRUD: Programación de Mantenimiento
# ============================================================================

def crear_programacion(
    equipo_id: int,
    frecuencia_mantenimiento: int,
    frecuencia_calibracion: int,
    unidad_frecuencia: str
) -> ProgramacionMantenimiento:
    """
    Crear una programación de mantenimiento para un equipo.

    Args:
        equipo_id (int): ID del equipo biomédico.
        frecuencia_mantenimiento (int): Frecuencia de mantenimiento.
        frecuencia_calibracion (int): Frecuencia de calibración.
        unidad_frecuencia (str): Unidad (dias, meses, anios).

    Returns:
        ProgramacionMantenimiento: Instancia de la programación.

    Raises:
        EquipoNotFound: Si el equipo no existe.
    """
    try:
        equipo = EquipoBiomedico.objects.get(id=equipo_id)
    except EquipoBiomedico.DoesNotExist:
        raise EquipoNotFound(equipo_id)

    programacion = ProgramacionMantenimiento.objects.create(
        equipo=equipo,
        frecuencia_mantenimiento=frecuencia_mantenimiento,
        frecuencia_calibracion=frecuencia_calibracion,
        unidad_frecuencia=unidad_frecuencia
    )

    # Calcular próximas fechas
    programacion.calcular_proxima_fecha()

    return programacion


def obtener_programacion(programacion_id: int) -> ProgramacionMantenimiento:
    """
    Obtener una programación de mantenimiento por su ID.

    Args:
        programacion_id (int): ID de la programación.

    Returns:
        ProgramacionMantenimiento: Instancia de la programación.

    Raises:
        ProgramacionNotFound: Si la programación no existe.
    """
    try:
        return ProgramacionMantenimiento.objects.get(id=programacion_id)
    except ProgramacionMantenimiento.DoesNotExist:
        raise ProgramacionNotFound(programacion_id)


def listar_programaciones_por_equipo(equipo_id: int) -> QuerySet:
    """
    Listar programaciones de un equipo específico.

    Args:
        equipo_id (int): ID del equipo biomédico.

    Returns:
        QuerySet: Programaciones del equipo.

    Raises:
        EquipoNotFound: Si el equipo no existe.
    """
    try:
        equipo = EquipoBiomedico.objects.get(id=equipo_id)
    except EquipoBiomedico.DoesNotExist:
        raise EquipoNotFound(equipo_id)

    return ProgramacionMantenimiento.objects.filter(
        equipo=equipo
    ).order_by('-created_at')


# ============================================================================
# Servicios de Negocio
# ============================================================================

def supervisar_mantenimiento(mantenimiento_id: int, aprobado_por_id: int = None):
    """
    Supervisar/aprobar un mantenimiento y obtener programaciones asociadas.

    Cambia el estado a 'aprobado' y retorna programaciones del equipo.

    Args:
        mantenimiento_id (int): ID del mantenimiento a supervisar.
        aprobado_por_id (int, optional): ID del usuario que aprueba.

    Returns:
        QuerySet: Programaciones de mantenimiento del equipo.

    Raises:
        MantenimientoNotFound: Si el mantenimiento no existe.
        ResponsableNotFound: Si aprobado_por_id no existe.
    """
    mantenimiento = obtener_mantenimiento(mantenimiento_id)

    mantenimiento.estado = "aprobado"
    if aprobado_por_id:
        try:
            Usuario.objects.get(id=aprobado_por_id)
            mantenimiento.aprobado_por_id = aprobado_por_id
        except Usuario.DoesNotExist:
            raise ResponsableNotFound(aprobado_por_id)

    mantenimiento.save()

    mensaje = (
        f"El mantenimiento para el equipo {mantenimiento.equipo.nombre} "
        f"ha sido aprobado."
    )
    if not _notificacion_existente(mensaje, mantenimiento.responsable.correo):
        _crear_notificacion(mensaje, mantenimiento.responsable.correo)
        _enviar_correo(mantenimiento.responsable.correo, mensaje)

    return ProgramacionMantenimiento.objects.filter(
        equipo=mantenimiento.equipo
    )


def generar_reporte_general() -> dict:
    """
    Generar reporte general de mantenimientos.

    Retorna conteos de equipos, mantenimientos, estado de ordenes de servicio.

    Returns:
        dict: Diccionario con estadísticas generales.
    """
    total_equipos = EquipoBiomedico.objects.count()
    total_mantenimientos = Mantenimiento.objects.count()
    mantenimientos_pendientes = Mantenimiento.objects.filter(
        estado="pendiente"
    ).count()
    ordenes_ejecutadas = OrdenServicio.objects.filter(
        estado="ejecutada"
    ).count()

    return {
        "totalEquipos": total_equipos,
        "totalMantenimientos": total_mantenimientos,
        "mantenimientosPendientes": mantenimientos_pendientes,
        "ordenesEjecutadas": ordenes_ejecutadas
    }