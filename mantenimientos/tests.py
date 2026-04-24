"""
Suite de pruebas para servicios de mantenimientos.

Covers:
- Creación, lectura, actualización de mantenimientos
- Validaciones de entrada y transiciones de estado
- Notificaciones por correo
- Órdenes de servicio y programaciones
"""

from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta

from usuarios.models import Usuario
from equipos.models import EquipoBiomedico, Ubicacion, Marca, Modelo
from mantenimientos.models import Mantenimiento, OrdenServicio, ProgramacionMantenimiento
from mantenimientos import services
from mantenimientos.exceptions import (
    MantenimientoNotFound,
    EquipoNotFound,
    ResponsableNotFound,
    EstadoInvalido,
    FechasInvalidas,
    DiagnosticoVacio,
    OrdenServicioNotFound,
    ProgramacionNotFound,
)


class BaseTest(TestCase):
    """Base class con helpers comunes para tests."""

    @staticmethod
    def crear_ubicacion(area="hemodinamia", detalle="Test Location"):
        """Helper para crear ubicaciones."""
        return Ubicacion.objects.create(
            sede="pabon",
            departamento="narino",
            ciudad="pasto",
            area=area,
            detalle=detalle
        )

    @staticmethod
    def crear_equipo(ubicacion, nombre="Test Equipo", serie="SN000001"):
        """Helper para crear equipos biomédicos."""
        marca = Marca.objects.create(nombre=f"Marca-{serie}")
        modelo = Modelo.objects.create(nombre=f"Modelo-{serie}", marca=marca)
        return EquipoBiomedico.objects.create(
            nombre=nombre,
            marca=marca,
            modelo=modelo,
            tipo_tecnologia="soporte_vital",
            serie=serie,
            ubicacion=ubicacion
        )


class MantenimientoServiceTest(BaseTest):
    """Tests para servicios CRUD de Mantenimiento."""

    def setUp(self):
        """Configurar datos de prueba."""
        # Crear ubicación
        self.ubicacion = self.crear_ubicacion(
            detalle="Piso 1 - Hemodinamia"
        )

        # Crear equipo
        self.equipo = self.crear_equipo(
            self.ubicacion,
            nombre="Desfibrilador DCF-100",
            serie="SN123456"
        )

        # Crear responsable
        self.responsable = Usuario.objects.create_user(
            correo="responsable@test.com",
            username="responsable",
            nombre="Juan Responsable",
            password="test123",
            rol="ingenierobiomedico",
            estado="activo"
        )

        # Crear usuario aprobador
        self.aprobador = Usuario.objects.create_user(
            correo="aprobador@test.com",
            username="aprobador",
            nombre="Carlos Aprobador",
            password="test123",
            rol="coordinador",
            estado="activo"
        )

        self.fecha_inicio = timezone.now()
        self.fecha_fin = self.fecha_inicio + timedelta(hours=2)

    def test_crear_mantenimiento_exitoso(self):
        """Test creación correcta de mantenimiento."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Revisión de funcionamiento general",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id,
            tipo='preventivo',
            fecha_fin=self.fecha_fin
        )

        self.assertIsNotNone(mantenimiento.id)
        self.assertEqual(mantenimiento.equipo.id, self.equipo.id)
        self.assertEqual(mantenimiento.responsable.id, self.responsable.id)
        self.assertEqual(mantenimiento.diagnostico, "Revisión de funcionamiento general")
        self.assertEqual(mantenimiento.estado, "pendiente")
        self.assertEqual(mantenimiento.tipo, "preventivo")

    def test_crear_mantenimiento_equipo_no_existe(self):
        """Test crear mantenimiento con equipo inexistente."""
        with self.assertRaises(EquipoNotFound):
            services.crear_mantenimiento(
                equipo_id=9999,
                diagnostico="Test",
                fecha_inicio=self.fecha_inicio,
                responsable_id=self.responsable.id
            )

    def test_crear_mantenimiento_responsable_no_existe(self):
        """Test crear mantenimiento con responsable inexistente."""
        with self.assertRaises(ResponsableNotFound):
            services.crear_mantenimiento(
                equipo_id=self.equipo.id,
                diagnostico="Test",
                fecha_inicio=self.fecha_inicio,
                responsable_id=9999
            )

    def test_crear_mantenimiento_diagnostico_vacio(self):
        """Test crear mantenimiento con diagnóstico vacío."""
        with self.assertRaises(DiagnosticoVacio):
            services.crear_mantenimiento(
                equipo_id=self.equipo.id,
                diagnostico="",
                fecha_inicio=self.fecha_inicio,
                responsable_id=self.responsable.id
            )

    def test_crear_mantenimiento_diagnostico_espacios_en_blanco(self):
        """Test crear mantenimiento con diagnóstico solo espacios."""
        with self.assertRaises(DiagnosticoVacio):
            services.crear_mantenimiento(
                equipo_id=self.equipo.id,
                diagnostico="   ",
                fecha_inicio=self.fecha_inicio,
                responsable_id=self.responsable.id
            )

    def test_crear_mantenimiento_fechas_invalidas(self):
        """Test crear mantenimiento con fecha_fin anterior a fecha_inicio."""
        fecha_fin_invalida = self.fecha_inicio - timedelta(hours=1)

        with self.assertRaises(FechasInvalidas):
            services.crear_mantenimiento(
                equipo_id=self.equipo.id,
                diagnostico="Test",
                fecha_inicio=self.fecha_inicio,
                responsable_id=self.responsable.id,
                fecha_fin=fecha_fin_invalida
            )

    def test_crear_mantenimiento_diagnostico_espacios_se_recorta(self):
        """Test que el diagnóstico con espacios al inicio/final se recorta."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="  Test diagnóstico  ",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        self.assertEqual(mantenimiento.diagnostico, "Test diagnóstico")

    def test_editar_mantenimiento_exitoso(self):
        """Test edición correcta de mantenimiento."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Diagnóstico original",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        datos_actualizacion = {
            "diagnostico": "Diagnóstico actualizado",
            "tipo": "correctivo"
        }

        mantenimiento_actualizado = services.editar_mantenimiento(
            mantenimiento.id,
            datos_actualizacion
        )

        self.assertEqual(
            mantenimiento_actualizado.diagnostico,
            "Diagnóstico actualizado"
        )
        self.assertEqual(mantenimiento_actualizado.tipo, "correctivo")

    def test_editar_mantenimiento_no_existe(self):
        """Test editar mantenimiento inexistente."""
        with self.assertRaises(MantenimientoNotFound):
            services.editar_mantenimiento(9999, {"diagnostico": "Test"})

    def test_editar_mantenimiento_diagnostico_vacio(self):
        """Test editar mantenimiento con diagnóstico vacío."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Original",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        with self.assertRaises(DiagnosticoVacio):
            services.editar_mantenimiento(mantenimiento.id, {"diagnostico": ""})

    def test_editar_mantenimiento_responsable_invalido(self):
        """Test editar mantenimiento con responsable inexistente."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        with self.assertRaises(ResponsableNotFound):
            services.editar_mantenimiento(
                mantenimiento.id,
                {"responsable_id": 9999}
            )

    def test_editar_mantenimiento_fechas_invalidas(self):
        """Test editar mantenimiento con fechas inconsistentes."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        fecha_fin_invalida = self.fecha_inicio - timedelta(hours=1)

        with self.assertRaises(FechasInvalidas):
            services.editar_mantenimiento(
                mantenimiento.id,
                {
                    "fecha_fin": fecha_fin_invalida
                }
            )

    def test_cambiar_estado_a_valido(self):
        """Test cambiar estado a un estado válido."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        mantenimiento_actualizado = services.cambiar_estado(
            mantenimiento.id,
            'en_proceso'
        )

        self.assertEqual(mantenimiento_actualizado.estado, 'en_proceso')

    def test_cambiar_estado_invalido(self):
        """Test cambiar estado a un estado inválido."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        with self.assertRaises(EstadoInvalido):
            services.cambiar_estado(mantenimiento.id, 'estado_invalido')

    def test_obtener_mantenimiento_existe(self):
        """Test obtener mantenimiento existente."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        mantenimiento_obtenido = services.obtener_mantenimiento(mantenimiento.id)

        self.assertEqual(mantenimiento_obtenido.id, mantenimiento.id)

    def test_obtener_mantenimiento_no_existe(self):
        """Test obtener mantenimiento inexistente."""
        with self.assertRaises(MantenimientoNotFound):
            services.obtener_mantenimiento(9999)

    def test_listar_mantenimientos(self):
        """Test listar todos los mantenimientos."""
        services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 1",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 2",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        mantenimientos = services.listar_mantenimientos()

        self.assertEqual(mantenimientos.count(), 2)

    def test_listar_por_equipo(self):
        """Test listar mantenimientos filtrados por equipo."""
        # Crear segundo equipo
        equipo2 = self.crear_equipo(
            self.ubicacion,
            nombre="Monitor ECG",
            serie="SN789012"
        )

        services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 1",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        services.crear_mantenimiento(
            equipo_id=equipo2.id,
            diagnostico="Test 2",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        mantenimientos = services.listar_por_equipo(self.equipo.id)

        self.assertEqual(mantenimientos.count(), 1)
        self.assertEqual(mantenimientos[0].equipo.id, self.equipo.id)

    def test_listar_por_equipo_no_existe(self):
        """Test listar por equipo inexistente."""
        with self.assertRaises(EquipoNotFound):
            services.listar_por_equipo(9999)

    def test_listar_por_responsable(self):
        """Test listar mantenimientos por responsable."""
        # Crear segundo responsable
        responsable2 = Usuario.objects.create_user(
            correo="responsable2@test.com",
            username="responsable2",
            nombre="Pedro Responsable",
            password="test123",
            rol="ingenierobiomedico",
            estado="activo"
        )

        services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 1",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 2",
            fecha_inicio=self.fecha_inicio,
            responsable_id=responsable2.id
        )

        mantenimientos = services.listar_por_responsable(self.responsable.id)

        self.assertEqual(mantenimientos.count(), 1)
        self.assertEqual(mantenimientos[0].responsable.id, self.responsable.id)

    def test_listar_por_responsable_no_existe(self):
        """Test listar por responsable inexistente."""
        with self.assertRaises(ResponsableNotFound):
            services.listar_por_responsable(9999)

    def test_listar_por_estado(self):
        """Test listar mantenimientos por estado."""
        mantenimiento1 = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 1",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        mantenimiento2 = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test 2",
            fecha_inicio=self.fecha_inicio,
            responsable_id=self.responsable.id
        )

        services.cambiar_estado(mantenimiento1.id, 'completado')

        mantenimientos_pendientes = services.listar_por_estado('pendiente')
        mantenimientos_completados = services.listar_por_estado('completado')

        self.assertEqual(mantenimientos_pendientes.count(), 1)
        self.assertEqual(mantenimientos_completados.count(), 1)

    def test_listar_por_estado_invalido(self):
        """Test listar por estado inválido."""
        with self.assertRaises(EstadoInvalido):
            services.listar_por_estado('estado_invalido')


class OrdenServicioServiceTest(BaseTest):
    """Tests para servicios de Orden de Servicio."""

    def setUp(self):
        """Configurar datos de prueba."""
        self.ubicacion = self.crear_ubicacion(detalle="Piso 2")

        self.equipo = self.crear_equipo(
            self.ubicacion,
            nombre="Ventilador Pulmonar",
            serie="SN654321"
        )

        self.responsable = Usuario.objects.create_user(
            correo="responsable@test.com",
            username="responsable",
            nombre="Juan Responsable",
            password="test123",
            rol="ingenierobiomedico",
            estado="activo"
        )

        self.mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Mantenimiento preventivo",
            fecha_inicio=timezone.now(),
            responsable_id=self.responsable.id
        )

    def test_crear_orden_servicio_exitosa(self):
        """Test creación correcta de orden de servicio."""
        orden = services.crear_orden_servicio(
            mantenimiento_id=self.mantenimiento.id,
            tipo_servicio="Limpieza y lubricación",
            descripcion="Limpieza completa del equipo",
            estado='pendiente'
        )

        self.assertIsNotNone(orden.id)
        self.assertEqual(orden.mantenimiento.id, self.mantenimiento.id)
        self.assertEqual(orden.tipo_servicio, "Limpieza y lubricación")
        self.assertEqual(orden.estado, 'pendiente')

    def test_crear_orden_servicio_mantenimiento_no_existe(self):
        """Test crear orden con mantenimiento inexistente."""
        with self.assertRaises(MantenimientoNotFound):
            services.crear_orden_servicio(
                mantenimiento_id=9999,
                tipo_servicio="Test",
                descripcion="Test"
            )

    def test_obtener_orden_servicio_existe(self):
        """Test obtener orden existente."""
        orden = services.crear_orden_servicio(
            mantenimiento_id=self.mantenimiento.id,
            tipo_servicio="Test",
            descripcion="Test"
        )

        orden_obtenida = services.obtener_orden_servicio(orden.id)

        self.assertEqual(orden_obtenida.id, orden.id)

    def test_obtener_orden_servicio_no_existe(self):
        """Test obtener orden inexistente."""
        with self.assertRaises(OrdenServicioNotFound):
            services.obtener_orden_servicio(9999)

    def test_listar_ordenes_por_mantenimiento(self):
        """Test listar órdenes de un mantenimiento."""
        services.crear_orden_servicio(
            mantenimiento_id=self.mantenimiento.id,
            tipo_servicio="Test 1",
            descripcion="Test 1"
        )

        services.crear_orden_servicio(
            mantenimiento_id=self.mantenimiento.id,
            tipo_servicio="Test 2",
            descripcion="Test 2"
        )

        ordenes = services.listar_ordenes_por_mantenimiento(self.mantenimiento.id)

        self.assertEqual(ordenes.count(), 2)

    def test_listar_ordenes_mantenimiento_no_existe(self):
        """Test listar órdenes de mantenimiento inexistente."""
        with self.assertRaises(MantenimientoNotFound):
            services.listar_ordenes_por_mantenimiento(9999)


class ProgramacionServiceTest(BaseTest):
    """Tests para servicios de Programación de Mantenimiento."""

    def setUp(self):
        """Configurar datos de prueba."""
        self.ubicacion = self.crear_ubicacion(detalle="Piso 3")

        self.equipo = self.crear_equipo(
            self.ubicacion,
            nombre="Incubadora Neonatal",
            serie="SN345678"
        )

    def test_crear_programacion_exitosa(self):
        """Test creación de programación de mantenimiento."""
        programacion = services.crear_programacion(
            equipo_id=self.equipo.id,
            frecuencia_mantenimiento=30,
            frecuencia_calibracion=90,
            unidad_frecuencia='dias'
        )

        self.assertIsNotNone(programacion.id)
        self.assertEqual(programacion.equipo.id, self.equipo.id)
        self.assertEqual(programacion.frecuencia_mantenimiento, 30)
        self.assertEqual(programacion.frecuencia_calibracion, 90)
        self.assertIsNotNone(programacion.proximo_mantenimiento)
        self.assertIsNotNone(programacion.proximo_calibracion)

    def test_crear_programacion_equipo_no_existe(self):
        """Test crear programación con equipo inexistente."""
        with self.assertRaises(EquipoNotFound):
            services.crear_programacion(
                equipo_id=9999,
                frecuencia_mantenimiento=30,
                frecuencia_calibracion=90,
                unidad_frecuencia='dias'
            )

    def test_obtener_programacion_existe(self):
        """Test obtener programación existente."""
        programacion = services.crear_programacion(
            equipo_id=self.equipo.id,
            frecuencia_mantenimiento=30,
            frecuencia_calibracion=90,
            unidad_frecuencia='dias'
        )

        programacion_obtenida = services.obtener_programacion(programacion.id)

        self.assertEqual(programacion_obtenida.id, programacion.id)

    def test_obtener_programacion_no_existe(self):
        """Test obtener programación inexistente."""
        with self.assertRaises(ProgramacionNotFound):
            services.obtener_programacion(9999)

    def test_listar_programaciones_por_equipo(self):
        """Test listar programaciones de un equipo."""
        services.crear_programacion(
            equipo_id=self.equipo.id,
            frecuencia_mantenimiento=30,
            frecuencia_calibracion=90,
            unidad_frecuencia='dias'
        )

        programaciones = services.listar_programaciones_por_equipo(self.equipo.id)

        self.assertEqual(programaciones.count(), 1)

    def test_listar_programaciones_equipo_no_existe(self):
        """Test listar programaciones de equipo inexistente."""
        with self.assertRaises(EquipoNotFound):
            services.listar_programaciones_por_equipo(9999)


class MantenimientoBusinessLogicTest(BaseTest):
    """Tests para lógica de negocio de mantenimientos."""

    def setUp(self):
        """Configurar datos de prueba."""
        self.ubicacion = self.crear_ubicacion(detalle="Piso 4")

        self.equipo = self.crear_equipo(
            self.ubicacion,
            nombre="Bomba de Infusión",
            serie="SN987654"
        )

        self.responsable = Usuario.objects.create_user(
            correo="responsable@test.com",
            username="responsable",
            nombre="Juan Responsable",
            password="test123",
            rol="ingenierobiomedico",
            estado="activo"
        )

        self.aprobador = Usuario.objects.create_user(
            correo="aprobador@test.com",
            username="aprobador",
            nombre="Carlos Aprobador",
            password="test123",
            rol="coordinador",
            estado="activo"
        )

    def test_supervisar_mantenimiento(self):
        """Test supervisión de mantenimiento."""
        mantenimiento = services.crear_mantenimiento(
            equipo_id=self.equipo.id,
            diagnostico="Test",
            fecha_inicio=timezone.now(),
            responsable_id=self.responsable.id
        )

        programaciones = services.supervisar_mantenimiento(
            mantenimiento.id,
            aprobado_por_id=self.aprobador.id
        )

        mantenimiento_actualizado = services.obtener_mantenimiento(mantenimiento.id)

        self.assertEqual(mantenimiento_actualizado.estado, 'aprobado')
        self.assertEqual(
            mantenimiento_actualizado.aprobado_por.id,
            self.aprobador.id
        )
        self.assertIsInstance(programaciones, type(
            ProgramacionMantenimiento.objects.all()
        ))

    def test_generar_reporte_general(self):
        """Test generación de reporte general."""
        reporte = services.generar_reporte_general()

        self.assertIn('totalEquipos', reporte)
        self.assertIn('totalMantenimientos', reporte)
        self.assertIn('mantenimientosPendientes', reporte)
        self.assertIn('ordenesEjecutadas', reporte)
        self.assertIsInstance(reporte['totalEquipos'], int)
