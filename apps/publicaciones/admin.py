from django.contrib import admin
from .models import Publicacion
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fecha_publicacion", "publicado", "autor")
    list_filter = ("publicado", "fecha_publicacion")
    search_fields = ("titulo", "autor__username")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si es una nueva publicación, establecer el autor como el usuario actual
        if not obj:
            form.base_fields["autor"].initial = request.user
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Si no es superusuario, mostrar solo las publicaciones del usuario actual
        if not request.user.is_superuser:
            qs = qs.filter(autor=request.user)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filtrar la lista de usuarios para mostrar solo staff
        if db_field.name == "autor":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Si es una nueva publicación, establecer el autor como el usuario actual
        if not change:
            obj.autor = request.user
        super().save_model(request, obj, form, change)

