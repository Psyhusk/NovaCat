<div align="center">

```
███╗   ██╗ ██████╗ ██╗   ██╗ █████╗  ██████╗ █████╗ ████████╗
████╗  ██║██╔═══██╗██║   ██║██╔══██╗██╔════╝██╔══██╗╚══██╔══╝
██╔██╗ ██║██║   ██║██║   ██║███████║██║     ███████║   ██║   
██║╚██╗██║██║   ██║╚██╗ ██╔╝██╔══██║██║     ██╔══██║   ██║   
██║ ╚████║╚██████╔╝ ╚████╔╝ ██║  ██║╚██████╗██║  ██║   ██║   
╚═╝  ╚═══╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   
```

### 🔴 `VELVET DAGGER` — Defensive Cyber Threat Intelligence

💜 Apoie o Desenvolvimento O NovaCat é um projeto de código aberto, arquitetado e desenvolvido 100% em ambiente mobile. Meu objetivo é criar ferramentas de alta performance que facilitem o fluxo de trabalho de profissionais da área, mesmo com as limitações técnicas do meu setup atual. Se esta ferramenta foi útil para você, considere apoiar o projeto: 👉 patreon.com/cw/Psyhusk/membership Seu apoio é fundamental para que eu possa continuar dedicando tempo integral ao desenvolvimento, à correção de bugs e à implementação de novas funcionalidades. Todo apoio é muito bem-vindo e me ajuda a manter este ecossistema vivo e em constante evolução. 🙏
[![Python](https://img.shields.io/badge/Python-3.8%2B-red?style=flat-square&logo=python&logoColor=white&color=8b0000)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Arch%20%7C%20Hyprland-red?style=flat-square&color=8b0000)](https://archlinux.org)
[![License](https://img.shields.io/badge/License-MIT-red?style=flat-square&color=8b0000)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-red?style=flat-square&color=cc1a1a)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Defensivo-red?style=flat-square&color=cc1a1a)](#)

> *"O histórico não esquece. Você sim."*

</div>

---

## 🐱 O que é o NovaCat?

**NovaCat** é uma ferramenta defensiva e consultiva de **Cyber Threat Intelligence (CTI)** com interface gráfica nativa para Linux. Ela consulta fontes públicas de reputação para verificar se um identificador de rede — IP, MAC, hash de arquivo ou domínio — possui histórico de uso malicioso.

Sem instalação de servidores. Sem banco de dados local. Sem painel web.  
**Só você, o alvo, e o histórico que ele deixou por aí.**

---

## ✨ Funcionalidades

### 🔍 Identificadores Suportados

| Tipo | Exemplos | O que consulta |
|------|----------|----------------|
| 🌐 **IPv4 / IPv6** | `1.2.3.4` · `2001:db8::1` | Geolocalização, ASN, ISP, flags TOR/VPN/Proxy, AbuseIPDB, OTX, ThreatFox |
| 🖧 **MAC Address** | `AA:BB:CC:DD:EE:FF` | Fabricante via OUI, detecção de MAC spoofing (locally-administered) |
| 🧬 **Hash MD5/SHA** | `d41d8cd9…` · `e3b0c442…` | MalwareBazaar, ThreatFox, VirusTotal (com chave gratuita) |
| 🌍 **Domínio** | `suspeito.example.com` | URLhaus, ThreatFox, resolução DNS |

---

### 🎯 Fontes de Inteligência

```
◈ ip-api.com         Geolocalização · ASN · Proxy/VPN/TOR detection  (sem chave)
◈ AlienVault OTX     Threat score · Atividades maliciosas             (sem chave)
◈ ThreatFox          IOCs · C2 · Malware mapping                      (sem chave)
◈ MalwareBazaar      Hashes · Famílias · Tags de malware              (sem chave)
◈ URLhaus            URLs maliciosas · Hosts de distribuição           (sem chave)
◈ MACVendors         OUI · Fabricante de placa de rede                (sem chave)
◈ AbuseIPDB          Score 0–100 · Relatos · Histórico de abuso       (chave gratuita*)
◈ VirusTotal         Multi-engine detection para hashes               (chave gratuita*)
```

> `*` Chaves gratuitas configuradas em `~/.novacat/config.json`

---

### 🩺 Vereditos

| Veredito | Cor | Critério |
|----------|-----|----------|
| 🔴 **MALICIOSO** | Vermelho | Detectado em MalwareBazaar, URLhaus, ThreatFox ou AbuseIPDB score ≥ 70 |
| 🟡 **SUSPEITO** | Amarelo | Score moderado, MAC locally-administered, múltiplas flags |
| 🟠 **OBSERVAR** | Laranja | Sinais fracos, hosting/VPN sem histórico grave |
| 🟢 **LIMPO** | Verde | Nenhuma fonte reportou atividade maliciosa |
| ⚪ **DESCONHECIDO** | Cinza | Sem dados suficientes para análise |

---

## 🎨 Interface

A interface do NovaCat foi projetada para ser **memorável**:

```
┌──────────────────────────────────────────────────────────────────────┐
│ ◈ NovaCat — v1.0.0 · VELVET DAGGER · Defensive Threat Intelligence  │
├──────────────────────────────────────────────────────────────────────┤
│                                          ║                           │
│  ALVO (IP · MAC · Hash · Domínio · NIC)  ║   😼 (olhos vermelhos)   │
│  ┌────────────────────────────┐ [▶ SCAN] ║                           │
│  └────────────────────────────┘          ║   ✦ pentagrama brilhante  │
│                                          ║                           │
│  VEREDITO   [ MALICIOSO      ] ████████  ║   ◈ sub-pentagramas      │
│  ─────────────────────────────────────── ║                           │
│  País:         Brasil                    ║   v1.0.0                  │
│  ISP:          AS12345 Empresa XYZ       ╟──────────────────────────║
│  Flags:        TOR · VPN                 ║                           │
│  AbuseIPDB:    87/100 · 142 relatos      ║  ✦ ✦ ✦ (bg pentagramas)  │
│  ThreatFox:    SIM ⚠ · Mirai botnet      ║                           │
│                                          ║                           │
├──────────────────────────────────────────╢                           │
│ ▌ LOG  [>>] Consultando… // O alvo nem sabe que está sendo analisado.│
└──────────────────────────────────────────────────────────────────────┘
```

**Destaques visuais:**
- 🖤 Fundo escuro translúcido com pentagramas animados no background
- 😼 Gato de olhos **vermelhos pulsantes** no painel lateral
- 🔺 Pentagrama principal com **red glow** animado abaixo do gato
- 🪟 Janela **frameless e arrastável** — sem barra de título
- 📋 Barra de log inferior com **piadas sarcásticas** após cada etapa

---

## 🛠️ Instalação

### Pré-requisitos

```bash
# Arch Linux / Hyprland
sudo pacman -S python tk python-psutil python-pillow

# Debian / Ubuntu
sudo apt install python3 python3-tk python3-pip

# Fedora
sudo dnf install python3 python3-tkinter python3-psutil
```

### Instalação via Installer GUI

```bash
# 1. Clone ou baixe os arquivos
git clone https://github.com/seu-usuario/novacat
cd novacat

# 2. Execute o installer
python novacat_installer.py
```

O installer cuida de tudo: dependências, launcher, `.desktop` entry e config padrão.

### Instalação Manual

```bash
# Copia o script e cria o launcher
mkdir -p ~/.local/share/novacat ~/.local/bin
cp NovaCat.py ~/.local/share/novacat/
echo '#!/bin/bash
exec python3 ~/.local/share/novacat/NovaCat.py "$@"' > ~/.local/bin/novacat
chmod +x ~/.local/bin/novacat

# Garante que ~/.local/bin está no PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Executável único (PyInstaller)

```bash
pip install pyinstaller Pillow psutil
python build_novacat.py

# Arch / Wayland / Hyprland
GDK_BACKEND=x11 ./dist/NovaCat
```

---

## ⚙️ Configuração

O NovaCat cria automaticamente `~/.novacat/config.json` na primeira execução:

```json
{
  "abuseipdb_key":  "",
  "virustotal_key": "",
  "theme":          "crimson",
  "comment":        "Adicione suas chaves API gratuitas aqui."
}
```

### Como obter as chaves gratuitas

| Serviço | Link | Limite gratuito |
|---------|------|-----------------|
| 🛡️ AbuseIPDB | [abuseipdb.com/api](https://www.abuseipdb.com/api) | 1.000 consultas/dia |
| 🦠 VirusTotal | [virustotal.com/gui/join-us](https://www.virustotal.com/gui/join-us) | 500 consultas/dia |

> Sem chaves, o NovaCat ainda consulta **6 fontes públicas** sem limitação.

---

## 🚀 Uso

```bash
# Abre a interface gráfica
novacat

# Ou diretamente
python NovaCat.py

# Wayland / Hyprland
GDK_BACKEND=x11 novacat
```

**Exemplos de consulta na interface:**

```
# IP suspeito
185.220.101.47

# Endereço MAC (detecta spoofing)
02:AA:BB:CC:DD:EE

# Hash de arquivo suspeito (MD5/SHA256)
d41d8cd98f00b204e9800998ecf8427e

# Domínio malicioso
phishing-login.suspeito.xyz
```

---

## 📁 Estrutura do Projeto

```
novacat/
├── 😼  NovaCat.py               — Ferramenta principal (GUI + motor de consulta)
├── 🔧  novacat_installer.py     — Installer gráfico
├── 🏗️  build_novacat.py         — Build script (PyInstaller)
├── 📖  README.md                — Este arquivo
└── ⚙️  ~/.novacat/
        └── config.json          — Chaves API e configurações (criado na instalação)
```

---

## 🔴 Fontes e Créditos

O NovaCat integra exclusivamente **APIs públicas e gratuitas**:

- [**AbuseIPDB**](https://www.abuseipdb.com) — Base colaborativa de IPs abusivos
- [**AlienVault OTX**](https://otx.alienvault.com) — Open Threat Exchange
- [**ThreatFox**](https://threatfox.abuse.ch) — IOC database da abuse.ch
- [**MalwareBazaar**](https://bazaar.abuse.ch) — Hash de malware da abuse.ch
- [**URLhaus**](https://urlhaus.abuse.ch) — URLs maliciosas da abuse.ch
- [**ip-api.com**](https://ip-api.com) — Geolocalização gratuita
- [**MACVendors**](https://macvendors.com) — Lookup de fabricante por OUI
- [**VirusTotal**](https://www.virustotal.com) — Multi-engine file/hash scanner

---

## ⚠️ Aviso Legal

```
NovaCat é uma ferramenta DEFENSIVA e CONSULTIVA.

Ela consulta apenas dados PÚBLICOS já disponíveis em bases abertas de
inteligência de ameaças. Não realiza varreduras ativas, não envia pacotes
para os alvos consultados, e não armazena dados localmente além de logs
de sessão.

O uso desta ferramenta é de responsabilidade exclusiva do operador.
Utilize apenas em ambientes e contextos nos quais você possui autorização.
```

---

## 🧱 Stack Técnica

| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.8+ |
| GUI | tkinter (nativo, sem dependências pesadas) |
| HTTP | `urllib` (stdlib, zero dependências externas) |
| Build | PyInstaller |
| Plataformas | Linux · Arch · Hyprland · X11 · Wayland |

---

<div align="center">

```
◈ ─────────────────────────────────────────────────── ◈
       NovaCat  v1.0.0  ·  VELVET DAGGER
   Defensive Threat Intelligence · Open Source
       "O histórico não esquece. Você sim."
◈ ─────────────────────────────────────────────────── ◈
```

**Feito para analistas que preferem saber antes de confiar.**

</div>
