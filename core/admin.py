from django.contrib import admin
from .models import Materia, Tarefa, Anotacao, Feedback

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'cor')

@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'materia', 'status', 'prioridade', 'ordem')
    list_filter = ('status', 'prioridade', 'materia')
    list_editable = ('status', 'ordem') # Permite editar rápido no admin

admin.site.register(Anotacao)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rating", "page", "short_comment", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("usuario__username", "comment", "page")
    list_select_related = ("usuario",)

    def short_comment(self, obj):
        return (obj.comment or "")[:80] or "-"
    short_comment.short_description = "Comentario"
