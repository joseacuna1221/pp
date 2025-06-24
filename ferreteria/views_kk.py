from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string

from .models import Boleta, Producto, Categoria, detalle_boleta, Pedido, DetallePedido
from .forms import ContactoForm, CustomUserProfileForm, ProductoForm, CustomUserCreationForm
from .serializers import ProductoSerializer
from ferreteria.carrito import Carrito

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

import bcchapi
from datetime import datetime
import random
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER



#Banco central
import requests
from requests.auth import HTTPProxyAuth

def obtener_valor_dolar():
    try:
        # Configuración de proxy (si es necesario en PythonAnywhere)
        proxies = {
            'http': 'http://proxy.server:3128',  # Reemplaza con el proxy correcto
            'https': 'http://proxy.server:3128',
        }
        auth = HTTPProxyAuth('usuario_proxy', 'contraseña_proxy')  # Si requiere autenticación

        # Tu lógica actual para consultar la API del Banco Central
        # Ejemplo (ajusta según tu implementación real):
        response = requests.get(
            "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx",
            params={
                'user': 'es.ibarra@duocuc.cl',
                'pass': 'Uwu7832!',
                'firstdate': '2025-06-23',
                'lastdate': '2025-06-23',
                'timeseries': 'F073.TCO.PRE.Z.D',
                'function': 'GetSeries'
            },
            proxies=proxies,
            auth=auth,
            timeout=10  # Evita esperas infinitas
        )
        response.raise_for_status()  # Lanza error si la respuesta no es 200 OK
        datos = response.json()
        return datos["valor_dolar"]  # Ajusta según la estructura real de la respuesta

    except Exception as e:
        print(f"Error al obtener el dólar: {e}")
        return 950  # Valor por defecto si falla
#Tienda y funcion banco Central
@login_required
def tienda(request):
    productos = Producto.objects.all()
    valor_dolar = obtener_valor_dolar()
    return render(request, 'tienda.html', {
        'productos': productos,
        "valor_dolar":valor_dolar
        })

#Carrito
def agregar_producto(request, id):
    carrito = Carrito(request)
    producto = Producto.objects.get(idProducto=id)
    if producto.stock > 0:
        carrito.agregar(producto)
        messages.success(request, "Producto añadido al carrito.")
    else:
        messages.error(request, "No hay suficiente stock.")
    return redirect('tienda')

def eliminar_producto(request, id):
    carrito = Carrito(request)
    producto = Producto.objects.get(idProducto=id)
    carrito.eliminar(producto)
    return redirect('tienda')

def restar_producto(request, id):
    carrito = Carrito(request)
    producto = Producto.objects.get(idProducto=id)
    carrito.restar(producto)
    return redirect('tienda')

def limpiar_carrito(request):
    carrito = Carrito(request)
    carrito.limpiar()
    return redirect('tienda')

#boleta
def generarBoleta(request):
    precio_total=0
    productos = []

    #Calculo de precio
    for key, value in request.session['carrito'].items():
        precio_total = precio_total + int(value['precio']) * int(value['cantidad'])
    boleta = Boleta(total = precio_total)
    boleta.save()

    #Validar stock
    for key, value in request.session['carrito'].items():
        producto = Producto.objects.get(idProducto=value['producto_id'])
        if producto.stock < value['cantidad']:
            messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
            return redirect('tienda')

    #Detalle boleta
    for key, value in request.session['carrito'].items():
            producto = Producto.objects.get(idProducto = value['producto_id'])
            cant = value['cantidad']
            subtotal = cant * int(value['precio'])
            detalle = detalle_boleta(id_boleta = boleta, id_producto = producto, cantidad = cant, subtotal = subtotal)
            detalle.save()
            producto.stock -= cant
            producto.save()
            productos.append(detalle)
    datos={
        'productos':productos,
        'fecha':boleta.fechaCompra,
        'total': boleta.total
    }
    request.session['boleta'] = boleta.id_boleta
    carrito = Carrito(request)
    carrito.limpiar()
    return render(request, 'detallepedido.html',datos)

#Correo
def enviar_correo(request):
    if request.method == 'POST':
        send_mail(
            subject='Asunto del correo',
            message='Este es el cuerpo del correo',
            from_email='pruebaskk1221@gmail.com',
            recipient_list=['kkroto1221@correo.com'],
            fail_silently=False,
        )
        return HttpResponseRedirect(reverse('correo_enviado'))
    return render(request, 'enviar.html')

webpay_transaction = Transaction(
    WebpayOptions(
        commerce_code='597055555532',
        api_key='579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C',
        integration_type=IntegrationType.TEST
    )
)

def generarPedido(request):
    # Validar carrito vacío primero
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, "No puedes realizar una compra con el carrito vacío.")
        return redirect('tienda')

    if request.method == 'POST':
        tipo_envio = request.POST.get('tipo_envio')
        medio_pago = request.POST.get('medio_pago')

        # Calcular precio total
        precio_total = sum(int(item['precio']) * int(item['cantidad']) for item in carrito.values())

        if tipo_envio == 'domicilio':
            precio_total += 5000

        # Validar stock
        for key, value in carrito.items():
            producto = Producto.objects.get(idProducto=value['producto_id'])
            if producto.stock < value['cantidad']:
                messages.error(request, f"No hay suficiente stock para {producto.nombre}.")
                return redirect('tienda')

        # Crear pedido (en estado pendiente para Webpay)
        pedido_obj = Pedido.objects.create(
            user=request.user,
            estado = 'creado',
            tipo_envio=tipo_envio,
            tipo_pago=medio_pago,
            total=precio_total
        )

        # Si el medio de pago es Webpay
        if medio_pago == 'webpay':
            try:
                buy_order = str(pedido_obj.id_pedido)
                session_id = str(random.randint(100000, 999999))
                return_url = f'http://{request.get_host()}/webpay/respuesta/'

                response = webpay_transaction.create(
                    buy_order=buy_order,
                    session_id=session_id,
                    amount=precio_total,
                    return_url=return_url
                )

                # Guardar datos importantes en sesión
                request.session['webpay_token'] = response['token']
                request.session['webpay_order'] = buy_order
                request.session['id_pedido'] = pedido_obj.id_pedido

                # Redirigir a Webpay
                return render(request, 'webpay_redirigir.html', {
                    'url': response['url'],
                    'token': response['token']
                })
            except Exception as e:
                messages.error(request, f"Error al conectar con Webpay: {str(e)}")
                return redirect('carrito')

        # Para otros métodos de pago
        else:

            return redirect('formulario_transferencia', id_pedido=pedido_obj.id_pedido)

    return redirect('carrito')


def generar_pdf_pedido(pedido, detalles):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Obtener estilos base y modificar solo lo necesario
    styles = getSampleStyleSheet()

    # Crear estilos personalizados solo si no existen
    if 'CustomTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        ))

    if 'CustomSubtitle' not in styles:
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=10
        ))

    elements = []

    # Título usando el estilo personalizado
    elements.append(Paragraph("FERRETERIA FERREMAS", styles['CustomTitle']))
    elements.append(Paragraph("COMPROBANTE DE PEDIDO", styles['CustomSubtitle']))
    elements.append(Spacer(1, 20))

    # Resto del código permanece igual...
    pedido_info = [
        ["N° Pedido:", str(pedido.id_pedido)],
        ["Fecha:", pedido.fecha_compra.strftime("%d/%m/%Y %H:%M")],
        ["Cliente:", pedido.user.username],
        ["Estado:", pedido.estado.capitalize()],
        ["Tipo de envío:", pedido.tipo_envio.capitalize()],
        ["Total:", f"${pedido.total:,}"],
    ]

    pedido_table = Table(pedido_info, colWidths=[100, 200])
    pedido_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(pedido_table)
    elements.append(Spacer(1, 30))

    # Detalles del pedido
    elements.append(Paragraph("Detalles del Pedido", styles['Heading2']))

    detalle_data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]
    for detalle in detalles:
        detalle_data.append([
            detalle.id_producto.nombre,
            str(detalle.cantidad),
            f"${int(detalle.subtotal/detalle.cantidad):,}",
            f"${detalle.subtotal:,}"
        ])

    detalle_table = Table(detalle_data, colWidths=[200, 80, 100, 100])
    detalle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(detalle_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def enviar_pedido_por_correo(pedido, detalles, destinatario):
    # Generar PDF
    pdf = generar_pdf_pedido(pedido, detalles)

    # Crear mensaje de correo
    subject = f'Confirmación de Pedido #{pedido.id_pedido} - Ferreteria Ferremas'
    body = render_to_string('email_pedido.html', {
        'pedido': pedido,
        'detalles': detalles,
    })

    email = EmailMessage(
        subject,
        body,
        'pruebaskk1221@gmail.com',  # Remitente
        [destinatario],             # Destinatario
    )
    email.content_subtype = "html"  # Para contenido HTML

    # Adjuntar PDF
    email.attach(
        f'pedido_{pedido.id_pedido}.pdf',
        pdf,
        'application/pdf'
    )

    email.send()

def procesar_pedido_completo(request, pedido_obj, carrito, estado_pedido='pagado'):
    # Crear detalles del pedido
    productos = []
    for key, value in carrito.items():
        producto = Producto.objects.get(idProducto=value['producto_id'])
        cant = value['cantidad']
        subtotal = cant * int(value['precio'])

        DetallePedido.objects.create(
            id_pedido=pedido_obj,
            id_producto=producto,
            cantidad=cant,
            subtotal=subtotal
        )

        producto.stock -= cant
        producto.save()
        productos.append(producto)

    # Actualizar estado del pedido
    pedido_obj.estado = estado_pedido
    pedido_obj.save()

    # Obtener detalles para el PDF y correo
    detalles = DetallePedido.objects.filter(id_pedido=pedido_obj)

    # Enviar correo con PDF adjunto
    try:
        enviar_pedido_por_correo(pedido_obj, detalles, request.user.email)
        messages.success(request, "Se ha enviado un correo con los detalles de tu pedido.")
    except Exception as e:
        messages.warning(request, f"Pedido completado, pero hubo un error al enviar el correo: {str(e)}")

    # Limpiar carrito
    carrito = Carrito(request)
    carrito.limpiar()

    # Mostrar confirmación
    return render(request, 'detallepedido.html', {
        'detalles': detalles,
        'fecha': pedido_obj.fecha_compra,
        'total': pedido_obj.total,
        'tipo_envio': pedido_obj.tipo_envio
    })


def webpay_respuesta(request):
    token = request.POST.get('token_ws') or request.GET.get('token_ws')

    if not token:
        messages.error(request, "Se cancelo la compra o hubo un error, por favor intente nuevamente")
        return redirect('tienda')

    try:
        # Confirmar transacción con Webpay
        response = webpay_transaction.commit(token)

        if response.get('status') == 'AUTHORIZED':
            # Pago exitoso
            pedido_id = request.session.get('id_pedido')
            pedido = Pedido.objects.get(id_pedido=pedido_id)

            # Verificar que el pedido no haya sido procesado antes
            if pedido.estado == 'creado':
                carrito = request.session.get('carrito', {})
                return procesar_pedido_completo(request, pedido, carrito)
            else:
                messages.success(request, "Pedido ya fue procesado anteriormente")
                return redirect('detallepedido', id=pedido.id_pedido)
        else:
            # Pago fallido
            messages.error(request, "El pago no pudo ser procesado. Por favor intenta nuevamente.")
            return redirect('productos')

    except Exception as e:
        messages.error(request, f"Error al procesar el pago: {str(e)}")
        return redirect('tienda')

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy



class customPasswordResetView(auth_views.PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'email_recuperacion.html'
    success_url = reverse_lazy('password_reset_done')

class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


def enviar_link_recuperacion(request, usuario):
    token = default_token_generator.make_token(usuario)
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    dominio = 'kkroto1221.pythonanywhere.com'
    link = f"https://{dominio}/reset-password-confirm/{uid}/{token}/"

    subject = 'Recuperación de contraseña - Ferretería Ferremas'
    body = render_to_string('email_recuperacion.html', {
        'usuario': usuario,
        'link': link,
    })

    email = EmailMessage(
        subject,
        body,
        'pruebaskk1221@gmail.com',
        [usuario.email],
    )
    email.content_subtype = "html"
    email.send()

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Pedido

def formulario_transferencia(request, id_pedido):
    pedido = get_object_or_404(Pedido, id_pedido=id_pedido)

    # Datos bancarios ficticios (compartidos para GET y POST si hay error)
    datos_bancarios = {
        'banco': 'Banco Ficticio',
        'tipo_cuenta': 'Cuenta Corriente',
        'numero_cuenta': '1234-5678-9012-3456',
        'rut_titular': '12.345.678-9',
        'nombre_titular': 'Ferretería Ferremas',
        'email_contacto': 'transferencias@ferremas.com',
        'monto': pedido.total
    }

    # --- MANEJO DE POST (envío del formulario) ---
    if request.method == 'POST':
        comprobante = request.FILES.get('comprobante')
        comentarios = request.POST.get('comentarios', '')

        # Validación básica
        if not comprobante:
            messages.error(request, "Debes subir un comprobante de transferencia")
            return render(request, 'formulario_transferencia.html', {
                'pedido': pedido,
                'datos_bancarios': datos_bancarios,
                'comentarios': comentarios
            })

        # Validar tipo de archivo (ejemplo básico)
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        if comprobante.content_type not in allowed_types:
            messages.error(request, "Formato de archivo no válido. Sube PDF, JPG o PNG")
            return render(request, 'formulario_transferencia.html', {
                'pedido': pedido,
                'datos_bancarios': datos_bancarios,
                'comentarios': comentarios
            })

        # Actualizar estado del pedido
        pedido.estado = 'pendiente_verificacion'
        pedido.save()

        try:
            # --- ENVÍO DE CORREO AL CLIENTE ---
            subject_cliente = f'Recibimos tu comprobante - Pedido #{pedido.id_pedido}'
            body_cliente = render_to_string('email_confirmacion_cliente.html', {
                'pedido': pedido,
                'usuario': request.user,
                'comentarios': comentarios,
                'datos_bancarios': datos_bancarios
            })

            email_cliente = EmailMessage(
                subject_cliente,
                body_cliente,
                'pruebaskk1221@gmail.com',  # Remitente
                [request.user.email],       # Destinatario
            )
            email_cliente.content_subtype = "html"
            email_cliente.attach(
                comprobante.name,
                comprobante.read(),
                comprobante.content_type
            )
            email_cliente.send()

            # --- ENVÍO DE CORREO AL ADMINISTRADOR ---
            subject_admin = f'Nuevo comprobante - Pedido #{pedido.id_pedido}'
            body_admin = render_to_string('email_notificacion_admin.html', {
                'pedido': pedido,
                'usuario': request.user,
                'comentarios': comentarios,
                'datos_bancarios': datos_bancarios
            })

            email_admin = EmailMessage(
                subject_admin,
                body_admin,
                'pruebaskk1221@gmail.com',  # Remitente
                ['pruebaskk1221@gmail.com'],  # Correo admin
            )
            email_admin.content_subtype = "html"
            comprobante.seek(0)  # Reiniciar lectura del archivo
            email_admin.attach(
                comprobante.name,
                comprobante.read(),
                comprobante.content_type
            )
            email_admin.send()

            messages.success(request, "¡Comprobante recibido! Hemos enviado un correo de confirmación.")
            return render(request, 'espera_confirmacion.html', {'pedido': pedido})

        except Exception as e:
            # Si falla el envío de correos pero el pedido se registró
            messages.warning(
                request,
                "Recibimos tu comprobante pero hubo un error al enviar los correos. " +
                f"Error: {str(e)}. Por favor contáctanos."
            )
            return render(request, 'espera_confirmacion.html', {'pedido': pedido})

    # --- MANEJO DE GET (mostrar formulario) ---
    return render(request, 'formulario_transferencia.html', {
        'pedido': pedido,
        'datos_bancarios': datos_bancarios
    })