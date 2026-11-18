from django.db import models

# Create your models here.

from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    ci_ruc = models.CharField("CI / RUC", max_length=20, unique=True)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    fecha_registro = models.DateField(auto_now_add=True)

    @property
    def cid(self):
        return f"CID-{self.pk:04d}"

    def __str__(self):
        return f"{self.cid} - {self.nombre}"


class Material(models.Model):
    nombre = models.CharField(max_length=100)
    unidad = models.CharField(max_length=20, help_text="Ej: metro, unidad, kg")
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=0)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def hay_stock(self):
        return self.stock_actual > 0

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("PRESUPUESTADO", "Presupuestado"),
        ("APROBADO", "Aprobado"),
        ("EN_EJECUCION", "En ejecución"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="pedidos")
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField("Descripción de la obra")
    largo_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ancho_m = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default="PENDIENTE")

    @property
    def color_estado(self):
        return {
            "PENDIENTE": "secondary",
            "PRESUPUESTADO": "info",
            "APROBADO": "success",
            "EN_EJECUCION": "primary",
            "FINALIZADO": "dark",
            "CANCELADO": "danger",
        }[self.estado]

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente.nombre}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="detalles")
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=0)  # precio al momento del pedido

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def stock_suficiente(self):
        return self.material.stock_actual >= self.cantidad

    def __str__(self):
        return f"{self.material.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        if not self.precio_unitario:
            self.precio_unitario = self.material.precio_unitario
        super().save(*args, **kwargs)


class Presupuesto(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="presupuesto")
    fecha = models.DateField(auto_now_add=True)
    mano_obra = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    validez_dias = models.PositiveIntegerField(default=15)
    aceptado = models.BooleanField(default=False)

    @property
    def total_materiales(self):
        return sum(d.subtotal for d in self.pedido.detalles.all())

    @property
    def total(self):
        return self.total_materiales + self.mano_obra

    def __str__(self):
        return f"Presupuesto del pedido #{self.pedido_id}"