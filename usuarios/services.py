from django.contrib.auth import authenticate
from .models import Usuario

def login_usuario(correo,password):

    user = authenticate(
        username=correo,
        password=password
    )

    return user  

def register_usuario(data):

    password = data.pop("password")

    usuario = Usuario(**data)

    usuario.set_password(password)

    usuario.save()

    return usuario