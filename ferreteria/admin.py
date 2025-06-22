from django.contrib import admin
from .models import Categoria, Producto, Contacto, Boleta, detalle_boleta, Pedido, DetallePedido
from .forms import ProductoForm

# Register your models here.

class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'categoria','stock']
    list_editable = ['precio']
    search_fields = ['nombre']
    list_filter = ['categoria']
    list_per_page = 6
    form = ProductoForm

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id_pedido','user','fecha_compra','estado','tipo_envio','total','tipo_pago')

class detallePedidoAdmin(admin.ModelAdmin):
    list_display = ('id_pedido','id_detalle_pedido','id_producto','cantidad','subtotal')

class BoletaAdmin(admin.ModelAdmin):
    list_display = ('id_boleta','total','fechaCompra')

class DetalleBoletaAdmin(admin.ModelAdmin):
    list_display = ('id_boleta','id_detalle_boleta','id_producto','cantidad','subtotal')

admin.site.register(Categoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Contacto)
admin.site.register(Pedido,PedidoAdmin)
admin.site.register(DetallePedido,detallePedidoAdmin)
admin.site.register(Boleta,BoletaAdmin)
admin.site.register(detalle_boleta,DetalleBoletaAdmin)