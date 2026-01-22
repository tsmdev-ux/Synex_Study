from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager


class Materia(models.Model):
    CORES_CHOICES = [
        ('#3B82F6', 'Azul'),
        ('#EF4444', 'Vermelho'),
        ('#10B981', 'Verde'),
        ('#F59E0B', 'Amarelo'),
        ('#8B5CF6', 'Roxo'),
        ('#EC4899', 'Rosa'),
        ('#6B7280', 'Cinza'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    cor = models.CharField(max_length=7, choices=CORES_CHOICES, default='#3B82F6')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nome"],
                name="uniq_materia_usuario_nome",
            ),
        ]


class Tarefa(models.Model):
    STATUS_CHOICES = (
        ('todo', 'A Fazer'),
        ('doing', 'Em Andamento'),
        ('review', 'Revisao'),
        ('done', 'Concluido'),
    )

    PRIORIDADE_CHOICES = (
        ('B', 'Baixa'),
        ('M', 'Media'),
        ('A', 'Alta'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')
    prioridade = models.CharField(max_length=1, choices=PRIORIDADE_CHOICES, default='M')
    ordem = models.PositiveIntegerField(default=0)
    data_entrega = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta = models.ForeignKey('MetaObjetivo', on_delete=models.SET_NULL, null=True, blank=True, related_name='tarefas')

    class Meta:
        ordering = ['ordem', '-created_at']
        indexes = [
            models.Index(fields=["usuario", "status", "ordem"], name="idx_tarefa_user_status_ordem"),
            models.Index(fields=["usuario", "data_entrega"], name="idx_tarefa_user_entrega"),
        ]

    def clean(self):
        errors = {}
        if self.materia and self.materia.usuario_id != self.usuario_id:
            errors["materia"] = "Materia deve pertencer ao mesmo usuario da tarefa."
        if self.meta and self.meta.usuario_id != self.usuario_id:
            errors["meta"] = "Meta deve pertencer ao mesmo usuario da tarefa."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.titulo


class Anotacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    favorito = models.BooleanField(default=False)

    PRIORIDADE_CHOICES = [
        ('A', 'Alta'),
        ('M', 'Media'),
        ('B', 'Baixa'),
    ]

    prioridade = models.CharField(max_length=1, choices=PRIORIDADE_CHOICES, default='B')
    fonte = models.URLField(blank=True, null=True, help_text="Link da documentacao ou artigo")
    tags = TaggableManager(blank=True)

    def __str__(self):
        return self.titulo

    class Meta:
        indexes = [
            models.Index(fields=["usuario", "materia"], name="idx_anotacao_user_materia"),
            models.Index(fields=["usuario", "favorito"], name="idx_anotacao_user_fav"),
            models.Index(fields=["usuario", "prioridade"], name="idx_anotacao_user_prioridade"),
        ]

    def clean(self):
        if self.materia and self.materia.usuario_id != self.usuario_id:
            raise ValidationError({"materia": "Materia deve pertencer ao mesmo usuario da anotacao."})


class MetaObjetivo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_alvo = models.DateField()
    concluida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    def progresso(self):
        total = self.tarefas.count()
        if total == 0:
            return 0
        concluidas = self.tarefas.filter(status='done').count()
        return int((concluidas / total) * 100)


class SessaoEstudo(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessoes')
    tarefa = models.ForeignKey(Tarefa, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessoes_estudo')
    duracao_min = models.PositiveIntegerField()
    data = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(duracao_min__gt=0),
                name="chk_sessao_estudo_duracao_min",
            ),
        ]
        indexes = [
            models.Index(fields=["usuario", "data"], name="idx_sessao_user_data"),
        ]

    def __str__(self):
        materia = self.materia.nome if self.materia else "Sem materia"
        return f"{self.usuario.username} - {materia} - {self.duracao_min} min"

    def clean(self):
        errors = {}
        if self.materia and self.materia.usuario_id != self.usuario_id:
            errors["materia"] = "Materia deve pertencer ao mesmo usuario da sessao."
        if self.tarefa and self.tarefa.usuario_id != self.usuario_id:
            errors["tarefa"] = "Tarefa deve pertencer ao mesmo usuario da sessao."
        if errors:
            raise ValidationError(errors)


class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    avatar = models.FileField(upload_to='avatars/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    premium_activated_at = models.DateTimeField(null=True, blank=True)
    premium_expires_at = models.DateTimeField(null=True, blank=True)

    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        # fallback: primeira letra do username via data-uri svg
        inicial = (self.usuario.username[:1] or "S").upper()
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96'><rect width='100%' height='100%' fill='%233b82f6'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='48' fill='white'>{inicial}</text></svg>"
        import base64
        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Subscription(models.Model):
    PROVIDER_CHOICES = [
        ("abacate", "Abacate Pay"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default="abacate")
    provider_id = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=32, default="created")
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="BRL")
    current_period_end = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription {self.provider_id or self.id} - {self.status}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_id"],
                condition=~Q(provider_id=""),
                name="uniq_subscription_provider_provider_id",
            ),
        ]
        indexes = [
            models.Index(fields=["usuario", "status"], name="idx_subscription_user_status"),
        ]


class Payment(models.Model):
    PROVIDER_CHOICES = [
        ("abacate", "Abacate Pay"),
    ]
    KIND_CHOICES = [
        ("one_time", "One time"),
        ("subscription", "Subscription"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default="abacate")
    provider_id = models.CharField(max_length=120, blank=True)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    status = models.CharField(max_length=32, default="created")
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="BRL")
    checkout_url = models.URLField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.provider_id or self.id} - {self.status}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_id"],
                condition=~Q(provider_id=""),
                name="uniq_payment_provider_provider_id",
            ),
        ]
        indexes = [
            models.Index(fields=["usuario", "status"], name="idx_payment_user_status"),
        ]


@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def salvar_perfil(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
