from django.urls import path, include
from . import views
from . import views_kk
from .views import ProductoViewset, CategoriaViewset
from rest_framework import routers

#Permite crear las url necesarias para nuestra app
router = routers.DefaultRouter()
router.register('producto', ProductoViewset) #Urls que genera router
router.register('categoria', CategoriaViewset)

urlpatterns=[
    path('', views.index, name="index"),
    path('perfil/', views.perfil, name="perfil"),
    path('logout/', views.cerrar, name="cerrar"),
    path('registrar/', views.registrar, name="registrar"),
    path('nosotros/', views.nosotros, name="nosotros"),
    path('detalle/<id>/', views.detalle_producto, name="detalle"),
    path('agregar/', views.agregar, name="agregar"),
    path('modificar/<id>/', views.modificar, name="modificar"),
    path('lista/', views.lista, name="lista"),

    # Bodega
    path('bodega/', views.orden_pedidos, name="bodega"),
    path('bodegaPedido/<id>', views.detalle_pedidos, name="bodegaPedido"),
    path('despachar/<id>',views.despachar, name="despachar"),

   #Administrador
    path('administrador/', views.admin_view, name="administrador"),
    path('detallepedido/<id>', views.detalle_pedidosAdmin, name="detallepedido"),
    path('exportar-informe/', views.exportar_reporte_mensual, name='exportar_informe'),
    path('panel/usuarios/', views.panel_admin_usuarios, name='admin_panel_usuarios'),
    #Estas son las vistas para modificar el estado de los pedidos, así que no sé si son necesarios
    path('panel/pedidos/', views.panel_admin_pedidos, name='admin_panel_pedidos'),
    path('panel/pedidos/<int:pedido_id>/', views.detalle_pedido_admin, name='detalle_pedido_admin'),
    path('panel/actualizar_estado_pedido/<int:id_pedido>/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),

    #Contador
    path('contadorTrans/', views.contadorTrans_view, name="contadorTrans"),  
    path('contador/', views.contador_view, name="contador"),
    path('cont_aprobar/<id>',views.cont_aprobar, name="cont_aprobar"),
    path('cont_rechazar/<id>',views.cont_rechazar, name="cont_rechazar"),

    #Vendedor
    path('vendedor/', views.vendedor_view, name="vendedor"),  
    path('vendedorDetalle/<id>', views.detalle_pedidosVendedor, name="vendedorDetalle"),
    path('entregas', views.entregas_view, name="entregas"),
    path('entregar/<id>',views.entregar, name="entregar"),
    path('preparar/<id>',views.preparar, name="preparar"),
    path('rechazar/<id>',views.rechazar, name="rechazar"),

    path('eliminar/<id>/', views.eliminar, name="eliminar"),  
    path('api/', include(router.urls)),

    path('tienda/', views_kk.tienda, name="tienda"),
    path('agregar/<id>', views_kk.agregar_producto, name="add"),
    path('eliminar/<id>', views_kk.eliminar_producto, name="del"),
    path('restar/<id>', views_kk.restar_producto, name="sub"),
    path('limpiar/', views_kk.limpiar_carrito, name="cls"),
    path('generarBoleta/', views_kk.generarBoleta,name="generarBoleta"),
    path('generarPedido/', views_kk.generarPedido,name="generarPedido"),
    path('webpay/iniciar/', views_kk.generarPedido, name='webpay_iniciar'),
    path('webpay/respuesta/', views_kk.webpay_respuesta, name='webpay_respuesta'),

    # contraseña
    path('reset-password/', views_kk.customPasswordResetView.as_view(), name='custom_password_reset'),
    path('reset-password/done/', views_kk.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset-password-confirm/<uidb64>/<token>/', views_kk.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset-password-complete/', views_kk.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('transferencia/<int:id_pedido>/', views_kk.formulario_transferencia, name='formulario_transferencia'),
     
]