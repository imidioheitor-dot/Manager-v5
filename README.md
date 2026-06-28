# 🛡️ Meeting Guardian

Agente de monitoramento de agenda com IA que envia resumos diários e lembretes automáticos via Slack e E-mail.

## Funcionalidades

- ✅ Resumo diário às 06:00 com IA (Claude)
- ✅ Lembretes automáticos 30 minutos antes de cada evento
- ✅ Classificação de eventos por categoria
- ✅ Detecção de conflitos de agenda
- ✅ Cálculo de carga de trabalho e blocos livres
- ✅ Envio via Slack DM e E-mail HTML responsivo
- ✅ Docker + docker-compose prontos para produção

## Estrutura

```
meeting-guardian/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── scheduler.py
│   ├── calendar_service.py
│   ├── slack_service.py
│   ├── email_service.py
│   ├── ai_summary_service.py
│   └── models.py
├── tests/
│   ├── test_calendar_service.py
│   ├── test_ai_summary_service.py
│   ├── test_email_service.py
│   └── test_slack_service.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Configuração Rápida

### 1. Google Calendar API
1. Acesse https://console.cloud.google.com/
2. Crie um projeto e ative a **Google Calendar API**
3. Crie credenciais OAuth 2.0 (Desktop App)
4. Baixe o JSON como `credentials.json`

### 2. Slack App
1. Acesse https://api.slack.com/apps → Create New App
2. Adicione os scopes: `chat:write`, `im:write`
3. Instale no workspace e copie o Bot Token (`xoxb-...`)
4. Copie seu User ID no Slack (perfil → Copy member ID)

### 3. Gmail App Password
1. Acesse sua conta Google → Segurança → Verificação em duas etapas
2. Gere uma **Senha de app** para "E-mail"
3. Use essa senha no `SMTP_PASSWORD`

### 4. Configurar e rodar

```bash
cp .env.example .env
# Edite o .env com suas credenciais

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Autenticação Google (abre o navegador uma vez)
python -c "from src.calendar_service import CalendarService; CalendarService()"

# Rodar testes
pytest tests/ -v

# Testar resumo manualmente
RUN_SUMMARY_ON_START=true python -m src.main
```

### 5. Deploy com Docker

```bash
docker-compose up -d --build
docker-compose logs -f
```

## Variáveis de Ambiente

| Variável | Descrição |
|---|---|
| `ANTHROPIC_API_KEY` | Chave da API Claude |
| `GOOGLE_CREDENTIALS_PATH` | Caminho para credentials.json |
| `SLACK_BOT_TOKEN` | Token do bot Slack (xoxb-...) |
| `SLACK_USER_ID` | ID do usuário Slack |
| `SMTP_USER` | E-mail Gmail |
| `SMTP_PASSWORD` | App Password do Gmail |
| `EMAIL_RECIPIENT` | E-mail destinatário |
| `USER_NAME` | Seu nome (usado nas mensagens) |
| `RUN_SUMMARY_ON_START` | Roda resumo ao iniciar (true/false) |

## Licença

MIT
