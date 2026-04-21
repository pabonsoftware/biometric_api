from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .models import EquipoBiomedico, CodigoQR,ArchivoAdjunto
from .serializers import EquipoBiomedicoSerializer,ArchivoAdjuntoSerializer

from .selectors import (
    obtener_equipos,
    obtener_equipo_por_id,
)

from .services import (
    crear_equipo,
    actualizar_equipo,
    eliminar_equipo
)

from .models import (
    Marca,
    Modelo,
    Fabricante,
    TipoTecnologia,
    Ubicacion
)

class EquipoBiomedicoViewSet(viewsets.ModelViewSet):

    serializer_class = EquipoBiomedicoSerializer

    def list(self,request):

        equipos = obtener_equipos()

        serializer = EquipoBiomedicoSerializer(equipos,many=True)

        return Response(serializer.data)
    
    def retrieve(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        serializer = EquipoBiomedicoSerializer(equipo)

        return Response(serializer.data)
    

    def parse_checkbox(data,opciones):
        return {op:bool(data.get(op,False)) for op in opciones}
    
    def create(self,request):

        data = request.data.copy()


        nueva_marca = request.data.get("nuevaMarca")
        if nueva_marca:
            marca = Marca.objects.create(nombre=nueva_marca)
            data["marca"] = marca.id

        nuevo_modelo = request.data.get("nuevoModelo")
        if nuevo_modelo:
            modelo = Modelo.objects.create(nombre=nuevo_modelo)
            data["modelo"] = modelo.id
            
        nueva_tecnologia = request.data.get("nuevaTecnologia")
        if nueva_tecnologia:
            tecnologia = TipoTecnologia.objects.create(nombre=nueva_tecnologia)
            data["tipoTecnologia"] = tecnologia.id
            
        nuevo_fabricante = request.data.get("nuevoFabricante")
        if nuevo_fabricante:
            fabricante = Fabricante.objects.create(nombre=nuevo_fabricante)
            data["fabricante"] = fabricante.id

        nueva_ubicacion = request.data.get("nuevaUbicacion")
        if nueva_ubicacion:
            ubicacion = Ubicacion.objects.create(
                sede="pabon",
                departamento="narino",
                ciudad="pasto",
                area="uci_6",
                detalle=data["nuevaUbicacion"]
            )
            data["ubicacion"] = ubicacion.id

        nuevo_equipo = request.data.get("nuevoEquipo")
        if nuevo_equipo:
            data["nombre"] = nuevo_equipo

        data["estado_equipo"] = {
            "bueno":bool(data.get("estado_bueno")),
            "regular":bool(data.get("estado_regular")),
            "malo":bool(data.get("estado_malo")),
            "desarmado":bool(data.get("estado_desarmado")),
        }

        data["tipo_mantenimiento"] = {
            "preventivo":bool(data.get("mant_preventivo")),
            "correctivo":bool(data.get("mant_correctivo")),
            "instalacion":bool(data.get("mant_instalacion")),
            "desmontaje":bool(data.get("mant_desmontaje"))
        }

        data["fallas"] = {
            "depreciacion":bool(data.get("falla_depreciacion")),
            "mala_operacion":bool(data.get("falla_mala_operacion")),
            "mal_instalado":bool(data.get("falla_mal_instalado")),
            "accesorios":bool(data.get("falla_accesorios")),
            "sin_fallas":bool(data.get("falla_sin_fallas"))
        }

        serializer = EquipoBiomedicoSerializer(data=data)

        if serializer.is_valid():

            equipo = crear_equipo(serializer.validated_data)

            return Response(
                EquipoBiomedicoSerializer(equipo).data,
                status=status.HTTP_201_CREATED
            )
        

        print(serializer.errors)
        
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    def update(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        serializer = EquipoBiomedicoSerializer(
            equipo,
            data=request.data
        )

        if serializer.is_valid():

            equipo = actualizar_equipo(
                equipo,
                serializer.validated_data
            )

            return Response(
                EquipoBiomedicoSerializer(equipo).data
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        eliminar_equipo(equipo)

        return Response(status=status.HTTP_204_NO_CONTENT)

    
    @action(detail=True,methods=["post"])
    def generar_qr(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        qr,creado = CodigoQR.objects.get_or_create(equipo=equipo)

        qr.save()

        return Response({
            "message":"QR generado correctamente",
            "equipo":equipo.id,
            "qr":qr.codigo.url
        })
    
    @action(detail=True,methods=["get"])
    def qr(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        qr = equipo.codigo_qr

        return Response({
            "equipo":equipo.id,
            "nombre":equipo.nombre,
            "qr":qr.codigo.url,
            "fechaGeneracion":qr.fechaGeneracion
        })
    
    @action(detail=True,methods=["post"])
    def adjuntar_archivo(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        serializer = ArchivoAdjuntoSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save(equipo=equipo)

            return Response(serializer.data,status=201)
        
        return Response(serializer.errors,status=400)
    
    @action(detail=True,methods=["get"])
    def archivos(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        archivos = equipo.archivos.all()

        serializer = ArchivoAdjuntoSerializer(
            archivos,
            many=True
        )

        return Response(serializer.data)