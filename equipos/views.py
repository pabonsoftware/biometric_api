from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from .models import EquipoBiomedico, CodigoQR,ArchivoAdjunto
from .serializers import EquipoBiomedicoSerializer,ArchivoAdjuntoSerializer

from .selectors import (
    obtener_equipos,
    obtener_equipo_por_id,
    buscar_equipo
)

from .services import (
    crear_equipo,
    actualizar_equipo,
    eliminar_equipo
)

class EquipoBiomedicoViewSet(viewsets.ModelViewSet):

    def list(self,request):

        nombre = request.query_params.get("nombre")
        serie = request.query_params.get("serie")
        marca = request.query_params.get("marca")
        modelo = request.query_params.get("modelo")
        ubicacion = request.query_params.get("ubicacion")

        equipos = buscar_equipo(
            nombre=nombre,
            serie=serie,
            marca=marca,
            modelo=modelo,
            ubicacion=ubicacion
        )

        serializer = EquipoBiomedicoSerializer(equipos,many=True)

    
    def retrieve(self,request,pk=None):

        equipo = obtener_equipo_por_id(pk)

        serializer = EquipoBiomedicoSerializer(equipo)

        return Response(serializer.data)
    
    def create(self,request):

        serializer = EquipoBiomedicoSerializer(data=request.data)

        if serializer.is_valid():

            equipo = crear_equipo(serializer.validated_data)

            return Response(
                EquipoBiomedicoSerializer(equipo).data,
                status=status.HTTP_201_CREATED
            )
        
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