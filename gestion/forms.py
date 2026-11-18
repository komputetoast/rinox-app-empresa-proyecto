from django import forms
from django.forms import inlineformset_factory
from .models import Cliente, Material, Pedido, DetallePedido, Presupuesto
from django.contrib.auth.forms import AuthenticationForm


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "ci_ruc", "telefono", "email", "direccion"]


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = "__all__"


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "descripcion", "largo_m", "ancho_m"]  # el estado cambia por acciones, no a mano


DetalleFormSet = inlineformset_factory(
    Pedido, DetallePedido,
    fields=["material", "cantidad"],
    extra=2, can_delete=True,
)


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ["mano_obra", "validez_dias"]

class LoginForm(AuthenticationForm):
    recordarme = forms.BooleanField(
        required=False,
        label="Mantener la sesión abierta",
    )