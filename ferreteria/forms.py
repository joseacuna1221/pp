from django import forms
from .models import Contacto, Producto
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .validators import MaxSizeFileValidator
from django.forms import ValidationError


class ContactoForm(forms.ModelForm):
   
    class Meta:
        model = Contacto
        fields = '__all__'

class ProductoForm(forms.ModelForm):

    nombre = forms.CharField(min_length=3, max_length=50)
    imagen = forms.ImageField(required=True, validators=[MaxSizeFileValidator(max_file_size=4)])
    precio = forms.IntegerField(min_value=1, max_value=3000000)
    # stock = forms.IntegerField(min_value=0)

    # def clean_nombre(self):
    #     nombre = self.cleaned_data['nombre']
    #     existe = Producto.objects.filter(nombre__iexact=nombre).exists()
    #     if existe:
    #         raise ValidationError("El nombre del producto ya existe")
        
    #     return nombre
    
    class Meta:
        model = Producto
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields =  fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2'] 

class CustomUserProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields =  fields = ['username', 'first_name', 'last_name', 'email', 'password'] 
