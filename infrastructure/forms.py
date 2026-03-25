from django import forms
from .models import VehicleRate

class VehicleRateForm(forms.ModelForm):
    class Meta:
        model = VehicleRate
        fields = ['vehicle_type', 'price_per_hour']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-input'}),
            'price_per_hour': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }
        labels = {
            'vehicle_type': 'Tipo de Vehículo',
            'price_per_hour': 'Precio por Hora',
        }