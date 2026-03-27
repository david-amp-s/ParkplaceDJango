from django import forms

class ClientForm(forms.Form):
    # Opciones para el select del HTML
    CLIENT_TYPES = [
        ('REGULAR', 'Cliente Regular'),
        ('SENA', 'Aprendiz SENA 🎓'),
        ('VISITANTE', 'Visitante Ocasional'),
    ]

    name = forms.CharField(max_length=100)
    client_type = forms.ChoiceField(choices=CLIENT_TYPES)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)

