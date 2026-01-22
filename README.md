# Synex Study Flow

Sistema de gestão de estudos com Kanban, metas, cronograma, anotações e dashboard. Inclui planos Free/Premium com fluxo de upgrade demo e integração com Abacate Pay.

## Visão rápida
- Público-alvo: estudantes/devs que precisam organizar estudo e produtividade.
- Recursos-chave: Kanban, cronograma, metas, timer, notas com tags, dashboard.
- Planos: Free (limite de tarefas) e Premium (ilimitado + export).

## Ferramentas e tecnologias usadas
- Backend: Django 6, Python 3.12+
- Banco: PostgreSQL
- Orquestração: Docker + Docker Compose
- Admin DB: pgAdmin
- Servidor app: gunicorn
- Frontend (app logado): Tailwind CSS + Font Awesome
- Landing/legais: Bootstrap 5 + Bootstrap Icons
- Gráficos: Chart.js
- Drag and drop: SortableJS
- Markdown: Python-Markdown + bleach (sanitização)
- Tags: django-taggit
- Imagens: Pillow
- Integração de pagamento: Abacate Pay (checkout/webhook)

## Pré-requisitos
- Python 3.12+
- Node não é necessário
- PostgreSQL local ou via Docker
- Docker/Docker Compose (opcional, recomendado)

## Configuração do ambiente (.env)
Crie um arquivo `.env` na raiz com as variáveis abaixo.

### Mínimo para rodar local
```
SECRET_KEY=troque-esta-chave
DEBUG=True

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=synexdb
DB_USER=postgres
DB_PASSWORD=postgres
```

### Produção (exemplo)
```
SECRET_KEY=chave-secreta-forte
DEBUG=False
ALLOWED_HOSTS=app.seudominio.com
CSRF_TRUSTED_ORIGINS=https://app.seudominio.com

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

DATABASE_URL=postgres://user:pass@host:5432/dbname
```

### E-mail (opcional)
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu@email.com
EMAIL_HOST_PASSWORD=sua_senha_app
DEFAULT_FROM_EMAIL=Synex System <no-reply@synex.dev>
```

### Premium demo / pagamento
```
PROMO_PREMIUM_CODE=PREMIUM-DEMO
PROMO_PREMIUM_DAYS=7

ABACATEPAY_API_URL=https://api.abacatepay.com/v1
ABACATEPAY_TOKEN=seu_token
ABACATEPAY_WEBHOOK_SECRET=seu_webhook_secret
ABACATEPAY_CURRENCY=BRL
ABACATEPAY_PREMIUM_PRICE_CENTS=2990
ABACATEPAY_ONE_TIME_PRICE_CENTS=2990
ABACATEPAY_ONE_TIME_DAYS=30
ABACATEPAY_CHECKOUT_PATH=checkout
ABACATEPAY_CANCEL_PATH=subscriptions/{subscription_id}/cancel
```

## Passo a passo (rodar local sem Docker)
1) Crie o banco no Postgres:
```
CREATE DATABASE synexdb;
```

2) Ative o venv:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3) Instale as dependências:
```
pip install -r requirements.txt
```

4) Configure o `.env` (exemplo mínimo acima).

5) Rode as migrações:
```
python manage.py migrate
```

6) Suba o servidor:
```
python manage.py runserver
```

7) Acesse:
- App: http://127.0.0.1:8000

## Passo a passo (rodar com Docker)
1) Configure `.env` (exemplo produção ou local).
2) Suba os containers:
```
docker compose build
docker compose up -d
```

3) Acesse:
- App: http://localhost:8000
- pgAdmin: http://localhost:5051

4) Registrar servidor no pgAdmin:
- Host: `db`
- Port: `5432`
- DB: `POSTGRES_DB`
- User/Pass: `POSTGRES_USER` / `POSTGRES_PASSWORD`

### Migrações (Docker)
```
docker compose exec web python manage.py migrate
```

### Backup automático (Docker)
O serviço `backup` gera dumps diários em `/backups` com retenção de 7 dias (volume `pgbackups`).
```
docker compose run --rm backup ls /backups
```

## Funcionalidades
- Autenticação completa (login/signup/reset) e e-mails de boas-vindas.
- Kanban com status: A Fazer, Estudando, Revisão, Concluído.
- Limite Free (3 tarefas) e upgrade por código promo (Premium).
- Dashboard com KPIs, gráficos e export JSON (Premium).
- Cronograma, metas e anotações com tags/favoritos.
- Perfil com avatar (validação de tamanho e tipo).

## Plano Free x Premium
- Free: até 3 tarefas, resto em modo leitura.
- Premium: tarefas ilimitadas + export.

## Segurança e produção
- Nunca commitar `.env` com segredos.
- Em produção: ative HTTPS e cookies seguros.
- Use `DATABASE_URL` para deploys gerenciados.

## Troubleshooting
- Erro `SECRET_KEY must be set in production`: defina `SECRET_KEY` e `DEBUG=True` no `.env`.
- Erro de conexão Postgres: confirme `DB_HOST`, `DB_PORT` e se o serviço está rodando.
- Migrações falhando: crie o banco antes e verifique permissões do usuário.

## Próximos passos sugeridos
- CI/CD com testes e migrações automatizadas.
- Checkout real em produção (Stripe/PagSeguro).
- CDN/Storage para estáticos e mídia (S3/GCS).
- Observabilidade (logs estruturados + Sentry).
