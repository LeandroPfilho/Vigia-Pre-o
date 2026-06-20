# Vigia de Preço

**Aviso importante** baixa compatibilidade com o mercado livre

O **Vigia de Preço** é uma aplicação web em Python/Flask para monitorar preços de produtos em sites de e-commerce, salvar o histórico em banco SQLite e enviar um e-mail quando houver queda de preço maior ou igual a **8%**.

O projeto foi organizado com arquitetura **MVC**, adaptada para Flask, e separado também em **Services** e **Repositories** para manter as responsabilidades bem divididas.

> Importante: este projeto não tenta burlar CAPTCHA, login, bloqueios, mecanismos antirobô ou sistemas de proteção. Sempre respeite os termos de uso dos sites. Quando existir API oficial, prefira a estratégia `api`.

---

## Tecnologias usadas

- Python 3
- Flask
- Jinja2
- Bootstrap 5
- BeautifulSoup
- Requests
- Selenium
- SQLite
- SQLAlchemy
- smtplib
- python-dotenv
- APScheduler
- logging

---

## Como a arquitetura MVC foi aplicada

### Models

Ficam na pasta `models/` e representam os dados principais do sistema:

- `Produto`
- `HistoricoPreco`
- `Alerta`

Os models não fazem scraping, não enviam e-mail e não exibem dados na tela.

### Views

Ficam na pasta `templates/` e são os arquivos HTML com Jinja2 e Bootstrap 5:

- `base.html`
- `index.html`
- `produtos.html`
- `produto_form.html`
- `historico.html`
- `alertas.html`
- `erro.html`

As views não possuem regra de negócio. Elas apenas exibem informações recebidas dos controllers.

### Controllers

Ficam na pasta `controllers/` e concentram as rotas Flask:

- Cadastro, edição, listagem e desativação de produtos
- Verificação manual de preços
- Visualização de histórico
- Visualização de alertas
- Dashboard

Os controllers não acessam diretamente banco, SMTP ou HTML externo. Eles chamam repositories e services.

### Services

Ficam na pasta `services/` e cuidam das regras e tarefas específicas:

- `scraper_service.py`: coleta preços com BeautifulSoup, Selenium ou API
- `price_service.py`: converte preços e calcula queda percentual
- `email_service.py`: envia alertas por e-mail
- `scheduler_service.py`: agenda verificações automáticas
- `monitoramento_service.py`: orquestra a verificação dos produtos

### Repositories

Ficam na pasta `repositories/` e concentram o acesso ao banco:

- Inserir produto
- Buscar produtos ativos
- Atualizar preços
- Salvar histórico
- Registrar alertas
- Consultar alertas enviados

---

## Como instalar

### 1. Crie o ambiente virtual

No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o `.env`

Copie o arquivo de exemplo:

```bash
copy .env.example .env
```

No Linux/Mac:

```bash
cp .env.example .env
```

Depois edite o `.env`:

```env
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
EMAIL_DESTINO=destino@email.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
REQUEST_TIMEOUT=10
REQUEST_RETRIES=3
INTERVALO_REQUISICOES_SEGUNDOS=5
INTERVALO_MONITORAMENTO_MINUTOS=60
FLASK_SECRET_KEY=troque-esta-chave
DATABASE_URL=sqlite:///vigia_preco.db
```

Para Gmail, normalmente é necessário usar **senha de app**, não a senha normal da conta.

### 4. Rode a aplicação

```bash
python app.py
```

Acesse no navegador:

```text
http://127.0.0.1:5000
```

---

## Como cadastrar produtos

Acesse **Produtos > Novo Produto** e informe:

- Nome do produto
- URL
- Seletor CSS do preço
- Estratégia de coleta
- Ativo ou inativo

Exemplo de seletor CSS:

```text
.price-tag-fraction
```

Cada site possui seu próprio HTML. Por isso, o seletor CSS precisa ser ajustado para cada página.

---

## Estratégias de coleta

### BeautifulSoup + Requests

Use quando o preço já aparece no HTML carregado pelo servidor.

Estratégia:

```text
beautifulsoup
```

### Selenium

Use quando o preço é carregado por JavaScript.

Estratégia:

```text
selenium
```

Para usar Selenium, você precisa ter navegador/driver compatível instalado. Em versões recentes, o Selenium Manager costuma ajudar a localizar o driver automaticamente.

### API oficial

Use quando o site disponibiliza uma API pública ou autorizada.

Estratégia:

```text
api
```

Neste projeto, o campo **seletor CSS** é reaproveitado como caminho JSON.

Exemplo de resposta da API:

```json
{
  "produto": {
    "preco": 299.90
  }
}
```

Nesse caso, informe:

```text
produto.preco
```

---

## Como verificar preços manualmente

Na tela de produtos, clique em:

```text
Verificar agora
```

Também é possível usar o botão no dashboard:

```text
Verificar todos agora
```

---

## Como funciona a execução automática

O APScheduler roda em segundo plano e verifica os produtos ativos de acordo com:

```env
INTERVALO_MONITORAMENTO_MINUTOS=60
```

O valor recomendado é usar intervalos seguros, como 1 hora ou mais.

Entre produtos diferentes, o sistema respeita:

```env
INTERVALO_REQUISICOES_SEGUNDOS=5
```

Isso evita requisições em massa.

---

## Como funciona o histórico de preços

Cada verificação cria um registro na tabela `historico_precos`, contendo:

- Produto
- Preço encontrado
- Data da verificação
- Status
- Mensagem de erro, quando existir

O histórico permite acompanhar evolução de preço ao longo do tempo.

---

## Como funciona o alerta de queda

O sistema compara:

```text
preço anterior x preço atual
```

A fórmula usada é:

```python
queda = ((preco_anterior - preco_atual) / preco_anterior) * 100
```

Se a queda for maior ou igual a **8%**, o sistema envia um e-mail com:

- Nome do produto
- Preço anterior
- Preço atual
- Percentual de queda
- Link do produto

Exemplo:

```text
Alerta de queda de preço!

Produto: Echo Dot 5ª geração
Preço anterior: R$ 349,90
Preço atual: R$ 299,90
Queda: 14,29%

Link: https://exemplo.com/produto
```

---

## Controle para evitar alertas repetidos

O sistema salva os alertas enviados na tabela `alertas` e também atualiza o campo `ultimo_alerta_enviado` do produto.

Antes de enviar um novo e-mail, ele verifica se já existe alerta recente/similar para:

- mesmo produto;
- mesmo preço anterior;
- mesmo preço atual;
- mesmo tipo de alerta.

Assim, evita vários e-mails repetidos para a mesma queda de preço.

---

## Timeout, retry e intervalo entre requisições

### Timeout

Controlado por:

```env
REQUEST_TIMEOUT=10
```

Se o site demorar mais que isso, a verificação falha com status de timeout.

### Retry

Controlado por:

```env
REQUEST_RETRIES=3
```

Se ocorrer erro temporário, o sistema tenta novamente.

### Intervalo entre produtos

Controlado por:

```env
INTERVALO_REQUISICOES_SEGUNDOS=5
```

O sistema aguarda alguns segundos antes de verificar o próximo produto.

---

## Status possíveis do produto

```text
ativo
inativo
erro_preco_nao_encontrado
erro_site_indisponivel
erro_timeout
erro_banco
verificado_com_sucesso
```

---

## Banco de dados

O banco inicial é SQLite e será criado automaticamente ao rodar a aplicação.

Tabelas principais:

- `produtos`
- `historico_precos`
- `alertas`

O projeto também cria produtos de teste automaticamente caso o banco esteja vazio.

---

## Observações importantes

- Não armazene senhas diretamente no código.
- Use `.env` para dados sensíveis.
- Não exponha dados sensíveis na interface.
- Não colete dados pessoais de usuários.
- Não faça requisições em massa.
- Sempre que possível, use APIs oficiais.

---

## Modos de cadastro: simples e avançado

Esta versão possui dois modos para cadastrar produtos.

### Modo simples

O modo simples foi criado para pessoas sem conhecimento técnico.

Fluxo de uso:

1. Acesse **Produtos > Novo Produto**;
2. Escolha **Modo simples**;
3. Informe o nome do produto;
4. Cole o link do produto;
5. Clique em **Detectar preço**;
6. Escolha o preço correto entre as opções encontradas;
7. Clique em **Salvar**.

Nesse modo, o sistema usa a estratégia `auto`. Ele tenta encontrar o preço sozinho usando:

- dados estruturados JSON-LD;
- meta tags de produto;
- elementos comuns de preço;
- textos que parecem preço, como `R$ 419,00`.

Se o botão de detecção não encontrar preço, ainda é possível salvar no modo simples. Na verificação manual ou automática, o sistema tentará detectar novamente.

### Modo avançado

O modo avançado mantém o funcionamento técnico original.

Use quando quiser informar manualmente:

- seletor CSS;
- estratégia `beautifulsoup`;
- estratégia `selenium`;
- estratégia `api`.

Exemplo de seletor CSS:

```text
.andes-money-amount__fraction
```

Exemplo para API, usando caminho JSON:

```text
produto.preco
```

### Quando usar cada modo?

Use **modo simples** quando o usuário só souber colar o link do produto.

Use **modo avançado** quando o modo simples não detectar o preço corretamente, quando o site carregar o preço de forma diferente ou quando você souber exatamente qual seletor CSS/API usar.

### Observação importante

A detecção automática facilita o uso, mas não garante funcionamento em todos os sites. Alguns e-commerces podem mudar o HTML, usar JavaScript pesado, bloquear automação ou exibir CAPTCHA. O projeto não tenta burlar proteções, login, CAPTCHA ou bloqueios.
