"""
Excepciones personalizadas para la aplicación de mantenimientos.

Define excepciones específicas del dominio de mantenimientos de equipos
biomédicos para manejo claro de errores en la capa de servicios.
"""


class MantenimientoException(Exception):
    """Excepción base para errores de mantenimientos."""
    pass


class MantenimientoNotFound(MantenimientoException):
    """Se lanza cuando no se encuentra un mantenimiento con el ID especificado."""

    def __init__(self, mantenimiento_id):
        self.mantenimiento_id = mantenimiento_id
        super().__init__(
            f"Mantenimiento con ID {mantenimiento_id} no encontrado."
        )


class EquipoNotFound(MantenimientoException):
    """Se lanza cuando no se encuentra un equipo biomédico."""

    def __init__(self, equipo_id):
        self.equipo_id = equipo_id
        super().__init__(
            f"Equipo biomédico con ID {equipo_id} no encontrado."
        )


class ResponsableNotFound(MantenimientoException):
    """Se lanza cuando no se encuentra el usuario responsable."""

    def __init__(self, responsable_id):
        self.responsable_id = responsable_id
        super().__init__(
            f"Usuario responsable con ID {responsable_id} no encontrado."
        )


class EstadoInvalido(MantenimientoException):
    """Se lanza cuando se intenta cambiar a un estado no válido."""

    def __init__(self, estado):
        self.estado = estado
        super().__init__(
            f"Estado '{estado}' no es válido. Debe ser uno de: "
            "pendiente, en_proceso, completado, aprobado, supervisado, ejecutado."
        )


class FechasInvalidas(MantenimientoException):
    """Se lanza cuando las fechas de inicio y fin son inconsistentes."""

    def __init__(self, fecha_inicio, fecha_fin):
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        super().__init__(
            f"Fecha de finalización ({fecha_fin}) no puede ser anterior "
            f"a la fecha de inicio ({fecha_inicio})."
        )


class DiagnosticoVacio(MantenimientoException):
    """Se lanza cuando el diagnóstico está vacío o en blanco."""

    def __init__(self):
        super().__init__("El diagnóstico no puede estar vacío o en blanco.")


class TransicionEstadoInvalida(MantenimientoException):
    """Se lanza cuando se intenta una transición de estado no permitida."""

    def __init__(self, estado_actual, nuevo_estado):
        self.estado_actual = estado_actual
        self.nuevo_estado = nuevo_estado
        super().__init__(
            f"No se puede transicionar de '{estado_actual}' a '{nuevo_estado}'."
        )


class OrdenServicioNotFound(MantenimientoException):
    """Se lanza cuando no se encuentra una orden de servicio."""

    def __init__(self, orden_id):
        self.orden_id = orden_id
        super().__init__(
            f"Orden de servicio con ID {orden_id} no encontrada."
        )


class ProgramacionNotFound(MantenimientoException):
    """Se lanza cuando no se encuentra una programación de mantenimiento."""

    def __init__(self, programacion_id):
        self.programacion_id = programacion_id
        super().__init__(
            f"Programación de mantenimiento con ID {programacion_id} no encontrada."
        )


class DatosInvalidos(MantenimientoException):
    """Se lanza cuando los datos proporcionados son inválidos."""

    def __init__(self, mensaje="Los datos proporcionados son inválidos."):
        super().__init__(mensaje)
