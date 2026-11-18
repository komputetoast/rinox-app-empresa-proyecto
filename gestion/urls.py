from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),

    path("clientes/", views.ClienteLista.as_view(), name="cliente_lista"),
    path("clientes/nuevo/", views.ClienteCrear.as_view(), name="cliente_crear"),
    path("clientes/<int:pk>/editar/", views.ClienteEditar.as_view(), name="cliente_editar"),

    path("materiales/", views.MaterialLista.as_view(), name="material_lista"),
    path("materiales/nuevo/", views.MaterialCrear.as_view(), name="material_crear"),
    path("materiales/<int:pk>/editar/", views.MaterialEditar.as_view(), name="material_editar"),

    path("pedidos/", views.PedidoLista.as_view(), name="pedido_lista"),
    path("pedidos/nuevo/", views.pedido_form, name="pedido_crear"),
    path("pedidos/<int:pk>/", views.pedido_detalle, name="pedido_detalle"),
    path("pedidos/<int:pk>/editar/", views.pedido_form, name="pedido_editar"),
    path("pedidos/<int:pk>/presupuesto/", views.presupuesto_form, name="presupuesto_form"),
    path("pedidos/<int:pk>/aprobar/", views.pedido_aprobar, name="pedido_aprobar"),

    path("clientes/<int:pk>/eliminar/", views.ClienteBorrar.as_view(), name="cliente_borrar"),
    path("materiales/<int:pk>/eliminar/", views.MaterialBorrar.as_view(), name="material_borrar"),
    path("pedidos/<int:pk>/eliminar/", views.pedido_borrar, name="pedido_borrar"),
    path("pedidos/<int:pk>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),
]