from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    model = Usuario

    list_display = (
        "id",
        "nombre",
        "correo",
        "rol",
        "estado",
        "is_staff"
    )
    search_fields = ("nombre","correo")
    ordering = ("correo",)

    fieldsets =  (
       (None, {"fields":("username","password")}),
       ("Información personal",{"fields":("nombre","correo")}),
       ("Permisos",{"fields": ( "is_active","is_staff", "is_superuser")},
       ),
       ("Fechas importantes",{"fields":("last_login","date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes":("wide",),
                "fields": (
                    "username",
                    "nombre",
                    "correo",
                    "rol",
                    "estado",
                    "password1",
                    "password2",
                ),
            },
        ),
    )