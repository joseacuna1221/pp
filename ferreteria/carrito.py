from django.shortcuts import render

class Carrito:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        carrito = self.session.get("carrito")
        if not carrito:
            carrito = self.session["carrito"] = {}
        self.carrito=carrito 
    
    def agregar(self, producto):
        if producto.idProducto not in self.carrito.keys():
            self.carrito[producto.idProducto]={
                "producto_id":producto.idProducto, 
                "nombre": producto.nombre,
                "precio": str (producto.precio),
                "cantidad": 1,
                "total": producto.precio,
            }
        else:
            self.carrito[producto.idProducto]["cantidad"] += 1
            self.carrito[producto.idProducto]["total"] += producto.precio
            # for key, value in self.carrito.items():
            #     if key==producto.idProducto:
            #         value["cantidad"] = value["cantidad"]+1
            #         value["precio"] = producto.precio
            #         value["total"]= value["total"] + producto.precio
            #         break
        self.guardar_carrito()


    def guardar_carrito(self):
        self.session["carrito"] = self.carrito
        self.session.modified=True

    def eliminar(self, producto):
        id = producto.idProducto
        if id in self.carrito: 
            del self.carrito[id]
            self.guardar_carrito()
    
    def restar (self,producto):
        idProducto = str(producto.idProducto)
        if idProducto in self.carrito:
            self.carrito[idProducto]["cantidad"] -= 1
            self.carrito[idProducto]["total"] -= producto.precio
            if self.carrito[idProducto]["cantidad"] < 1:
                self.eliminar(producto)
            self.guardar_carrito()
        # for key, value in self.carrito.items():
        #     if key in self.carrito:
        #         self.carrito[key]["cantidad"]
        #         value["cantidad"] = value["cantidad"]-1
        #         value["total"] = int(value["total"])- producto.precio
        #         if value["cantidad"] < 1:   
        #             self.eliminar(producto)
        #         break
        # self.guardar_carrito()
     
    def limpiar(self):
        self.session["carrito"]={}
        self.session.modified=True 
    
    def calcularTotal(self):
        total = 0
        for item in self.carrito.values():
            total += int(item["total"])
        return total
    
