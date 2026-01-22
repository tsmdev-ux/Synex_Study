from django.contrib import admin
from .models import Materia, Tarefa, Anotacao

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'cor')

@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'materia', 'status', 'prioridade', 'ordem')
    list_filter = ('status', 'prioridade', 'materia')
    list_editable = ('status', 'ordem') # Permite editar rápido no admin

admin.site.register(Anotacao)