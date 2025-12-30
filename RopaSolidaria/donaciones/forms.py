from django import forms
from .models import Prenda, CentroAcopio

class PrendaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar centros que NO estén en vacaciones y que NO estén llenos
        centros_disponibles = [
            c.id for c in CentroAcopio.objects.all() 
            if not c.en_vacaciones and not c.esta_lleno()
        ]
        self.fields['centro'].queryset = CentroAcopio.objects.filter(id__in=centros_disponibles)
    class Meta:
        model = Prenda
        fields = ['centro', 'tipo', 'talla', 'condicion', 'fecha_entrega', 'foto1', 'foto2', 'foto3']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}), # Cambiado a Select
            'talla': forms.Select(attrs={'class': 'form-select'}),
            'condicion': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto1': forms.FileInput(attrs={'class': 'form-control'}),
            'foto2': forms.FileInput(attrs={'class': 'form-control'}),
            'foto3': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'foto1': 'Foto Principal (Obligatoria)',
            'foto2': 'Foto Extra 1 (Opcional)',
            'foto3': 'Foto Extra 2 (Opcional)',
        }