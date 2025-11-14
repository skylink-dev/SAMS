from django import forms
from dal import autocomplete
from .models import ASM

class ASMForm(forms.ModelForm):
    class Meta:
        model = ASM
        fields = '__all__'
        widgets = {
            'partners': autocomplete.ModelSelect2Multiple(url='partner-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Change label for user field to ASM
        if 'user' in self.fields:
            self.fields['user'].label = "ASM"
