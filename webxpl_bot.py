# webxpl_bot.py
"""
Web XPL Bot - minimal Telegram bot for web reconnaissance commands:
  /nmap <host>  - simple TCP port scan (common ports)
  /gau <domain> - uses 'gau' CLI if present, otherwise extracts links from homepage (fallback)
  /crt <domain> - queries crt.sh JSON for certificates/subdomains
  /whois <domain> - optional (requires python-whois installed)
Run: set env var TG_TOKEN (or edit the variable below for quick testing).
"""

import os
import socket
import subprocess
import textwrap
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== Configuration =====
TELEGRAM_TOKEN = os.environ.get("TG_TOKEN")  # set this env var (recommended)
TELEGRAM_TOKEN = "8417965340:AAFKe4EpwnV8QveAVZwr0Qe-WpZYqXwnaPY"  # <-- alternative: paste token (not recommended for production)

COMMON_PORTS = [21,22,23,25,53,80,110,139,143,443,445,3306,3389,8080,8443]

# ===== Helper functions =====
def scan_host(host: str, ports=COMMON_PORTS, timeout=1.0):
    """Return list of open ports as strings like '80/tcp OPEN'."""
    results = []
    for p in ports:
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((host, p))
            s.close()
            results.append(f"{p}/tcp OPEN")
        except Exception:
            # closed or filtered
            pass
    return results

def gau_cli(domain: str, timeout=20):
    """Try to run 'gau' CLI. Returns stdout or raises FileNotFoundError if not installed."""
    proc = subprocess.run(["gau", domain], capture_output=True, text=True, timeout=timeout)
    output = proc.stdout.strip() or proc.stderr.strip()
    return output

def gau_fallback(domain: str, timeout=10):
    """Simple passive fallback: fetch homepage and extract links."""
    try:
        if not domain.startswith("http"):
            url = "https://" + domain
        else:
            url = domain
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        hrefs = set()
        for a in soup.find_all("a", href=True):
            hrefs.add(a["href"])
        # normalize: take up to 200 links
        lines = []
        for h in sorted(hrefs):
            lines.append(h)
            if len(lines) >= 200:
                break
        return "\n".join(lines) if lines else "Nenhum link encontrado na homepage."
    except Exception as e:
        return f"Erro ao buscar homepage: {e}"

def query_crtsh(domain: str, timeout=10):
    """Query crt.sh for domain JSON and return set of name_values."""
    q = f"%25.{domain}" if "." in domain else domain
    url = f"https://crt.sh/?q={q}&output=json"
    r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
    if r.status_code != 200:
        return None, f"crt.sh retornou status {r.status_code}"
    try:
        data = r.json()
    except ValueError:
        return None, "Resposta crt.sh não é JSON."
    subs = set()
    for item in data:
        name = item.get("name_value")
        if not name:
            continue
        for n in name.split("\n"):
            if domain in n:
                subs.add(n.strip())
    return sorted(subs), None

# ===== Command handlers =====
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Web XPL Bot ativo. Comandos: /nmap /gau /crt (opcional: /whois)")

async def nmap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /nmap <host>\nEx: /nmap example.com")
        return
    host = context.args[0]
    msg = await update.message.reply_text(f"Escaneando {host} (portas comuns)... isso pode levar alguns segundos.")
    try:
        open_ports = scan_host(host)
        if not open_ports:
            text = f"Nenhuma porta comum aberta detectada em {host}."
        else:
            text = "Portas abertas:\n" + "\n".join(open_ports)
    except Exception as e:
        text = f"Erro durante o scan: {e}"
    await msg.edit_text(text)

async def gau_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /gau <dominio>\nEx: /gau example.com")
        return
    domain = context.args[0]
    info_msg = await update.message.reply_text(f"Coletando URLs para {domain} ... (tentando 'gau', depois fallback)")
    # Try gau CLI
    try:
        out = gau_cli(domain)
        out = out.strip()
        if not out:
            out = "Comando 'gau' executado, mas não retornou resultados."
    except FileNotFoundError:
        out = None
    except Exception as e:
        out = f"Erro ao executar 'gau': {e}"

    if out is None:
        # fallback to simple homepage link extraction
        out = gau_fallback(domain)

    # Trim long outputs
    if len(out) > 3500:
        out = out[:3500] + "\n\n[Saída truncada]"
    await info_msg.edit_text(out)

async def crt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /crt <dominio>\nEx: /crt example.com")
        return
    domain = context.args[0]
    msg = await update.message.reply_text(f"Consultando crt.sh para {domain} ...")
    subs, err = query_crtsh(domain)
    if err:
        await msg.edit_text(f"Erro: {err}")
        return
    if not subs:
        await msg.edit_text("Nenhum subdomínio encontrado no crt.sh.")
    else:
        text = "Subdomínios encontrados (crt.sh):\n" + "\n".join(subs[:200])
        if len(text) > 4000:
            text = text[:3900] + "\n\n[Saída truncada]"
        await msg.edit_text(text)

# Optional: whois command if python-whois installed
async def whois_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /whois <dominio>")
        return
    try:
        import whois
    except Exception:
        await update.message.reply_text("Módulo python-whois não instalado. Instale com: pip install python-whois")
        return
    domain = context.args[0]
    msg = await update.message.reply_text(f"Consultando whois para {domain} ...")
    try:
        w = whois.whois(domain)
        out = []
        for k, v in w.items():
            out.append(f"{k}: {v}")
            if len("\n".join(out)) > 3800:
                break
        await msg.edit_text("\n".join(out))
    except Exception as e:
        await msg.edit_text(f"Erro whois: {e}")

# ===== Main =====
def main():
    token = TELEGRAM_TOKEN
    if not token:
        print("Erro: defina a variável de ambiente TG_TOKEN com o token do seu bot.")
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("nmap", nmap_cmd))
    app.add_handler(CommandHandler("gau", gau_cmd))
    app.add_handler(CommandHandler("crt", crt_cmd))
    app.add_handler(CommandHandler("whois", whois_cmd))
    print("Bot rodando. Pressione Ctrl+C para parar.")
    app.run_polling()

if __name__ == "__main__":
    main()
