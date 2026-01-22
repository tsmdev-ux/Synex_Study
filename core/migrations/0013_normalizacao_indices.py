from django.db import migrations, models
import django.db.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_perfil_premium_expires_at_subscription_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tarefa',
            name='data_entrega',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name='materia',
            constraint=models.UniqueConstraint(fields=('usuario', 'nome'), name='uniq_materia_usuario_nome'),
        ),
        migrations.AddIndex(
            model_name='tarefa',
            index=models.Index(fields=['usuario', 'status', 'ordem'], name='idx_tarefa_user_status_ordem'),
        ),
        migrations.AddIndex(
            model_name='tarefa',
            index=models.Index(fields=['usuario', 'data_entrega'], name='idx_tarefa_user_entrega'),
        ),
        migrations.AddIndex(
            model_name='anotacao',
            index=models.Index(fields=['usuario', 'materia'], name='idx_anotacao_user_materia'),
        ),
        migrations.AddIndex(
            model_name='anotacao',
            index=models.Index(fields=['usuario', 'favorito'], name='idx_anotacao_user_fav'),
        ),
        migrations.AddIndex(
            model_name='anotacao',
            index=models.Index(fields=['usuario', 'prioridade'], name='idx_anotacao_user_prioridade'),
        ),
            migrations.AddConstraint(
                model_name='sessaoestudo',
                constraint=models.CheckConstraint(condition=django.db.models.Q(('duracao_min__gt', 0)), name='chk_sessao_estudo_duracao_min'),
            ),
        migrations.AddIndex(
            model_name='sessaoestudo',
            index=models.Index(fields=['usuario', 'data'], name='idx_sessao_user_data'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.UniqueConstraint(condition=~django.db.models.Q(('provider_id', '')), fields=('provider', 'provider_id'), name='uniq_subscription_provider_provider_id'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['usuario', 'status'], name='idx_subscription_user_status'),
        ),
        migrations.AddConstraint(
            model_name='payment',
            constraint=models.UniqueConstraint(condition=~django.db.models.Q(('provider_id', '')), fields=('provider', 'provider_id'), name='uniq_payment_provider_provider_id'),
        ),
        migrations.AddIndex(
            model_name='payment',
            index=models.Index(fields=['usuario', 'status'], name='idx_payment_user_status'),
        ),
    ]
