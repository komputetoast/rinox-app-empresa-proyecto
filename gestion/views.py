from django.shortcuts import render

# Create your views here.

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.views import LoginView
from .forms import (ClienteForm, MaterialForm, PedidoForm,
                    DetalleFormSet, PresupuestoForm, LoginForm)
from .models import Cliente, Material, Pedido
from django.db.models import F, ProtectedError
from django.views.generic import ListView, CreateView, UpdateView, DeleteView


@login_required
def inicio(request):
    contexto = {
        "pedidos_pendientes": Pedido.objects.filter(estado="PENDIENTE").count(),
        "total_clientes": Cliente.objects.count(),
        "stock_bajo": Material.objects.filter(stock_actual__lte=F("stock_minimo")),
    }
    return render(request, "gestion/inicio.html", contexto)


# ---------- Clientes ----------
class ClienteLista(LoginRequiredMixin, ListView):
    model = Cliente
    ordering = ["nombre"]


class ClienteCrear(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "gestion/form.html"
    success_url = reverse_lazy("cliente_lista")
    extra_context = {"titulo": "Nuevo cliente"}


class ClienteEditar(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = "gestion/form.html"
    success_url = reverse_lazy("cliente_lista")
    extra_context = {"titulo": "Editar cliente"}


# ---------- Materiales ----------
class MaterialLista(LoginRequiredMixin, ListView):
    model = Material
    ordering = ["nombre"]


class MaterialCrear(LoginRequiredMixin, CreateView):
    model = Material
    form_class = MaterialForm
    template_name = "gestion/form.html"
    success_url = reverse_lazy("material_lista")
    extra_context = {"titulo": "Nuevo material"}


class MaterialEditar(LoginRequiredMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    template_name = "gestion/form.html"
    success_url = reverse_lazy("material_lista")
    extra_context = {"titulo": "Editar material"}

# ---------- Pedidos ----------
class PedidoLista(LoginRequiredMixin, ListView):
    model = Pedido
    ordering = ["-fecha", "-id"]


@login_required
def pedido_detalle(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    detalles = pedido.detalles.select_related("material")
    faltantes = [d for d in detalles if not d.stock_suficiente]
    return render(request, "gestion/pedido_detalle.html", {
        "pedido": pedido,
        "detalles": detalles,
        "faltantes": faltantes,
        "presupuesto": getattr(pedido, "presupuesto", None),
    })


@login_required
def pedido_form(request, pk=None):
    pedido = get_object_or_404(Pedido, pk=pk) if pk else None

    if pedido and pedido.estado not in ("PENDIENTE", "PRESUPUESTADO"):
        messages.error(request, "Un pedido aprobado o cancelado no se puede editar.")
        return redirect("pedido_detalle", pk=pedido.pk)

    form = PedidoForm(request.POST or None, instance=pedido)
    formset = DetalleFormSet(request.POST or None, instance=pedido)

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        pedido = form.save()
        formset.instance = pedido
        formset.save()
        messages.success(request, "Pedido guardado.")
        return redirect("pedido_detalle", pk=pedido.pk)

    return render(request, "gestion/pedido_form.html",
                  {"form": form, "formset": formset})


# ---------- Presupuesto ----------
@login_required
def presupuesto_form(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    presupuesto = getattr(pedido, "presupuesto", None)
    form = PresupuestoForm(request.POST or None, instance=presupuesto)

    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.pedido = pedido
        p.save()
        if pedido.estado == "PENDIENTE":
            pedido.estado = "PRESUPUESTADO"
            pedido.save()
        messages.success(request, "Presupuesto guardado.")
        return redirect("pedido_detalle", pk=pedido.pk)

    return render(request, "gestion/form.html",
                  {"form": form, "titulo": f"Presupuesto del pedido #{pedido.pk}"})


# ---------- Aprobar (descuenta stock) ----------
@login_required
@require_POST
def pedido_aprobar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if pedido.estado != "PRESUPUESTADO":
        messages.error(request, "El pedido debe estar presupuestado para aprobarlo.")
        return redirect("pedido_detalle", pk=pk)

    with transaction.atomic():
        detalles = list(pedido.detalles.select_related("material"))
        faltantes = [d.material.nombre for d in detalles if not d.stock_suficiente]
        if faltantes:
            messages.error(request, "Stock insuficiente: " + ", ".join(faltantes))
            return redirect("pedido_detalle", pk=pk)

        for d in detalles:
            d.material.stock_actual -= d.cantidad
            d.material.save()

        pedido.estado = "APROBADO"
        pedido.save()
        pedido.presupuesto.aceptado = True
        pedido.presupuesto.save()

    messages.success(request, "Pedido aprobado y stock descontado.")
    return redirect("pedido_detalle", pk=pk)

# ---------- Eliminar clientes y materiales ----------
class BorrarProtegido(LoginRequiredMixin, DeleteView):
    template_name = "gestion/confirmar_borrar.html"

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "No se puede eliminar: tiene pedidos asociados.")
            return redirect(self.success_url)
        messages.success(self.request, "Eliminado correctamente.")
        return response


class ClienteBorrar(BorrarProtegido):
    model = Cliente
    success_url = reverse_lazy("cliente_lista")


class MaterialBorrar(BorrarProtegido):
    model = Material
    success_url = reverse_lazy("material_lista")


# ---------- Eliminar y cancelar pedidos ----------
@login_required
def pedido_borrar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if pedido.estado not in ("PENDIENTE", "PRESUPUESTADO", "CANCELADO"):
        messages.error(request, "Este pedido ya descontó stock. Cancelalo antes de eliminarlo.")
        return redirect("pedido_detalle", pk=pk)

    if request.method == "POST":
        pedido.delete()
        messages.success(request, "Pedido eliminado.")
        return redirect("pedido_lista")

    return render(request, "gestion/confirmar_borrar.html", {"object": pedido})


@login_required
@require_POST
def pedido_cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)

    if pedido.estado not in ("PENDIENTE", "PRESUPUESTADO", "APROBADO"):
        messages.error(request, "Este pedido no se puede cancelar.")
        return redirect("pedido_detalle", pk=pk)

    with transaction.atomic():
        if pedido.estado == "APROBADO":  # devolver el stock descontado
            for d in pedido.detalles.select_related("material"):
                d.material.stock_actual += d.cantidad
                d.material.save()
        pedido.estado = "CANCELADO"
        pedido.save()

    messages.success(request, "Pedido cancelado.")
    return redirect("pedido_detalle", pk=pk)

# ---------- Login con "mantener sesión" ----------
class Ingreso(LoginView):
    template_name = "registration/login.html"   # <- antes decía gestion/login.html
    authentication_form = LoginForm

    def form_valid(self, form):
        response = super().form_valid(form)   # <- super(), no self
        if form.cleaned_data.get("recordarme"):
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        return response