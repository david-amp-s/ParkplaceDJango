from django import forms

class ClientForm(forms.Form):

    CLIENT_TYPES = [
        ('REGULAR', 'Cliente Regular'),
        ('SENA', 'Aprendiz SENA 🎓'),
    ]

    name = forms.CharField(max_length=100)
    client_type = forms.ChoiceField(choices=CLIENT_TYPES)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField(required=False)

