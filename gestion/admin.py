from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Cliente, Material, Pedido, DetallePedido, Presupuesto


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    inlines = [DetalleInline]
    list_display = ("id", "cliente", "fecha", "estado")


admin.site.register(Cliente)
admin.site.register(Material)
admin.site.register(Presupuesto)