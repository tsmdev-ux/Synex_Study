from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Landing pÃºblica
    path('', views.landing_page, name='root'),
    path('home', views.landing_page, name='home'),
    path('home/', views.home_redirect, name='home_redirect'),

    # Ãrea logada
    path('board/', views.kanban_view, name='kanban'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # AutenticaÃ§Ã£o
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('upgrade/', views.upgrade_view, name='upgrade'),
    path('assinatura/', views.assinatura_view, name='assinatura'),
    path('configuracoes/', views.configuracoes_view, name='configuracoes'),

    # RecuperaÃ§Ã£o de senha
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="core/password_reset.html"
    ), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name="core/password_reset_sent.html"
    ), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="core/password_reset_confirm.html"
    ), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name="core/password_reset_complete.html"
    ), name="password_reset_complete"),

    # Ferramentas
    path('foco/', views.foco_view, name='foco'),
    path('cronograma/', views.cronograma_view, name='cronograma'),
    path('anotacoes/', views.anotacoes_list, name='anotacoes_list'),
    path('anotacoes/nova/', views.anotacao_edit, name='anotacao_create'),
    path('anotacoes/editar/<int:id>/', views.anotacao_edit, name='anotacao_edit'),
    path('anotacoes/ler/<int:id>/', views.anotacao_detail, name='anotacao_detail'),
    path('anotacoes/excluir/<int:id>/', views.anotacao_delete, name='anotacao_delete'),
    path('metas/', views.metas_list, name='metas_list'),
    path('metas/<int:id>/', views.meta_detail, name='meta_detail'),
    path('materias/', views.materias_list, name='materias_list'),
    path('materias/delete/<int:id>/', views.materia_delete, name='materia_delete'),

    # APIs
    path('api/mover/', views.api_mover_tarefa, name='api_mover_tarefa'),
    path('api/calendar/', views.api_tarefas_calendar, name='api_calendar'),
    path('api/favoritar/', views.api_toggle_favorito, name='api_toggle_favorito'),
    path('api/export/tarefas/', views.api_export_tarefas, name='api_export_tarefas'),
    path('api/calendar/study/', views.api_study_calendar, name='api_study_calendar'),
    path('api/feedback/', views.api_feedback, name='api_feedback'),


    path('payments/abacate/checkout/', views.abacate_checkout_view, name='abacate_checkout'),
    path('payments/abacate/webhook/', views.abacate_webhook, name='abacate_webhook'),

    # PWA
    path('sw.js', views.service_worker, name='service_worker'),

    # Manutencao
    path('manutencao/', views.manutencao_view, name='manutencao'),

    # Legais
    path('termos/', views.termos_view, name='termos'),
    path('privacidade/', views.privacidade_view, name='privacidade'),
    path('feedbacks/', views.feedbacks_view, name='feedbacks'),
]

