from django import forms
from PIL import Image
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Tarefa, Anotacao, MetaObjetivo, Materia, SessaoEstudo, Perfil


class TarefaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['materia'].queryset = Materia.objects.filter(usuario=user)

    class Meta:
        model = Tarefa
        fields = ['titulo', 'descricao', 'materia', 'prioridade', 'data_entrega', 'meta']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Ex: Estudar Algebra Linear'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-lg', 'rows': 3, 'placeholder': 'Detalhes da tarefa...'}),
            'materia': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'prioridade': forms.Select(attrs={'class': 'w-full p-2 border rounded-lg'}),
            'data_entrega': forms.DateInput(attrs={'class': 'w-full p-2 border rounded-lg', 'type': 'date'}),
        }


class AnotacaoForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['materia'].queryset = Materia.objects.filter(usuario=user)

    class Meta:
        model = Anotacao
        fields = ['titulo', 'materia', 'prioridade', 'fonte', 'tags', 'conteudo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Titulo da Anotacao'}),
            'materia': forms.Select(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg bg-white'}),
            'conteudo': forms.Textarea(attrs={'class': 'w-full p-3 border rounded-lg'}),
            'prioridade': forms.Select(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500'}),
            'fonte': forms.URLInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'https://...'}),
            'tags': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Ex: erro, deploy, tutorial'}),
        }


class MetaForm(forms.ModelForm):
    class Meta:
        model = MetaObjetivo
        fields = ['titulo', 'descricao', 'data_alvo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg'}),
            'descricao': forms.Textarea(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'rows': 3}),
            'data_alvo': forms.DateInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'type': 'date'}),
        }


class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nome', 'cor']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Ex: Docker, Matematica...'}),
            'cor': forms.RadioSelect(),
        }


class SessaoEstudoForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['materia'].queryset = Materia.objects.filter(usuario=user)
            self.fields['tarefa'].queryset = Tarefa.objects.filter(usuario=user)

    class Meta:
        model = SessaoEstudo
        fields = ['materia', 'tarefa', 'duracao_min', 'data']
        widgets = {
            'materia': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg bg-white'}),
            'tarefa': forms.Select(attrs={'class': 'w-full p-3 border rounded-lg bg-white'}),
            'duracao_min': forms.NumberInput(attrs={'class': 'w-full p-3 border rounded-lg', 'min': 1}),
            'data': forms.DateInput(attrs={'class': 'w-full p-3 border rounded-lg', 'type': 'date'}),
        }


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'w-full p-3 border rounded-lg bg-white'})
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        # 2 MB
        max_size = 2 * 1024 * 1024
        if avatar.size > max_size:
            raise forms.ValidationError("A imagem deve ter no máximo 2MB.")
        valid_mime = {'image/jpeg', 'image/png', 'image/webp'}
        content_type = getattr(avatar, 'content_type', '')
        if content_type not in valid_mime:
            raise forms.ValidationError("Formato inválido. Use JPEG, PNG ou WEBP.")
        try:
            avatar.seek(0)
            img = Image.open(avatar)
            img.verify()
        except Exception:
            raise forms.ValidationError("Arquivo de imagem invǭlido ou corrompido.")
        finally:
            avatar.seek(0)
        return avatar


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full p-3 border rounded-lg bg-white',
        'placeholder': 'seu@email.com'
    }))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
