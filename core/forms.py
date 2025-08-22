from django import forms
from .models import (
    AlunoPessoal, AlunoResponsaveis, AlunoContato,
    AlunoEscolar, AlunoComplementar
)

class AlunoPessoalForm(forms.ModelForm):
    class Meta:
        model = AlunoPessoal
        fields = '__all__'

class AlunoResponsaveisForm(forms.ModelForm):
    class Meta:
        model = AlunoResponsaveis
        fields = '__all__'

class AlunoContatoForm(forms.ModelForm):
    class Meta:
        model = AlunoContato
        fields = '__all__'

class AlunoEscolarForm(forms.ModelForm):
    class Meta:
        model = AlunoEscolar
        fields = '__all__'

class AlunoComplementarForm(forms.ModelForm):
    class Meta:
        model = AlunoComplementar
        fields = '__all__'
