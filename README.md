Web XPL Bot

Um bot simples em Python para o Telegram que implementa comandos de reconhecimento ativo e passivo úteis em pentests web.

Ele foi desenvolvido para a disciplina de Segurança e tem como objetivo demonstrar como automatizar tarefas comuns de enumeração em forma de bot.

📂 Estrutura do Bot
Bot_Xpl/
├── webxpl_bot.py        # Código principal do bot (comandos /nmap, /gau, /crt, /whois opcional)
├── requirements.txt      # Dependências necessárias para rodar
└── README.md             # Documentação do projeto

Principais comandos implementados:

/start → Mensagem inicial com ajuda.

/nmap <host> → Faz um escaneamento simples de portas comuns (não usa o Nmap, apenas sockets Python).

/gau <domínio> → Tenta usar a ferramenta gau (GetAllURLs) se instalada; caso contrário, faz fallback básico coletando links da homepage.

/crt <domínio> → Consulta crt.sh
 para descobrir certificados e subdomínios relacionados.

/whois <domínio> (opcional) → Executa consulta WHOIS (requer instalar python-whois).

⚙️ Como Rodar Localmente
1. Pré-requisitos

Python 3.10+ instalado.

Uma conta no Telegram e um bot criado no BotFather (você receberá um token de acesso).

2. Clonar ou copiar o projeto
git clone <link_do_repositório>
cd Bot_Xpl

3. Criar e ativar ambiente virtual

No Linux/macOS:

python3 -m venv venv
source venv/bin/activate


No Windows (cmd.exe):

python -m venv venv
venv\Scripts\activate.bat

4. Instalar dependências
pip install -r requirements.txt

5. Definir o token do bot

Substitua SEU_TOKEN_AQUI pelo token do BotFather.

No Linux/macOS:

export TG_TOKEN=SEU_TOKEN_AQUI


No Windows (cmd.exe):

set TG_TOKEN=SEU_TOKEN_AQUI

6. Rodar o bot
python webxpl_bot.py


Se tudo der certo, verá:

Bot rodando. Pressione Ctrl+C para parar.


Agora, abra o Telegram no celular, procure o seu bot (https://t.me/USERNAME_DO_SEU_BOT) e envie /start.

💻 Exemplos de Uso dos Comandos

No chat do Telegram com o bot:

/start


Resposta:

Web XPL Bot ativo. Comandos: /nmap /gau /crt (opcional: /whois)

/nmap example.com


Resposta (exemplo):

Portas abertas:
80/tcp OPEN
443/tcp OPEN

/crt example.com


Resposta (exemplo):

Subdomínios encontrados (crt.sh):
www.example.com
mail.example.com
shop.example.com

/gau example.com


Resposta (exemplo - fallback):

https://example.com/login
https://example.com/contact
https://example.com/products

/whois example.com


(se python-whois estiver instalado)
Resposta (trecho):

domain_name: example.com
registrar: IANA
creation_date: 1995-08-13
