#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   NovaCat  v1.0.0  —  VELVET DAGGER                                 ║
║   Defensive Threat Intelligence · IP · MAC · NIC · Hash · Domain    ║
║   "Porque às vezes o alvo nem sabe que é o alvo."                   ║
╚══════════════════════════════════════════════════════════════════════╝

Ferramenta defensiva e consultiva de inteligência de ameaças.
Consulta histórico público de IPs, MACs, NICs, hashes e domínios
para identificar indicadores de comprometimento (IOCs).

Fontes: AbuseIPDB · Shodan · MACVendors · VirusTotal · ThreatFox
"""

import os, sys, json, math, time, socket, threading, subprocess, re, hashlib
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime

# ── Tk/CustomTk ──────────────────────────────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
except ImportError:
    print("[!] tkinter ausente. sudo pacman -S tk  ou  sudo apt install python3-tk")
    sys.exit(1)

try:
    import psutil  # porque saber quem está conectado é sempre educativo
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# ── Paleta — Nada diz "confiança" como vermelho sangue num fundo negro ─
BG      = "#050303"   # tão escuro quanto a consciência do alvo
BG2     = "#090404"
BG3     = "#100606"
BG4     = "#150808"
GLOW1   = "#cc1a1a"   # vermelho de alerta — ou de vergonha alheia
GLOW2   = "#ff3333"
GLOW3   = "#ff6060"
GLOW4   = "#ff9999"   # rosa suficiente para o alvo se sentir exposto
BORDER  = "#8b0000"
TEXT    = "#f2e0e0"
MUTED   = "#7a5050"
DIM     = "#4a3030"
SUCCESS = "#22c55e"   # verde — raramente visto nesses logs
DANGER  = "#ef4444"
WARNING = "#f59e0b"
INFO    = "#60a5fa"
MONO    = "#ff8888"   # cor do terminal quando as coisas ficam interessantes

VERSION  = "1.0.0"
NAME     = "NovaCat"
CODENAME = "VELVET DAGGER"

# ── Piadas do log — porque CTI não precisa ser monótono ──────────────
LOG_JOKES = [
    # após consulta de IP
    "// IP verificado. Surpresa ou não — depende do quão otimista você é.",
    "// Dados retornados. O alvo provavelmente acha que é invisível.",
    "// Consulta completa. Spoiler: inocência é rara nessa faixa de score.",
    "// Resultado obtido. Quem diria que portas abertas atraem visitas.",
    "// Análise concluída. O histórico não mente, só omite às vezes.",
    # após geolocalização
    "// Geolocalização: porque o mundo é pequeno e os logs são eternos.",
    "// País identificado. Todo mundo tem que estar em algum lugar.",
    "// ASN mapeado. Infraestrutura tem dono, mesmo quando nega.",
    # após verificação MAC/NIC
    "// Fabricante identificado. Hardware não tem álibi.",
    "// OUI consultado. A placa de rede sabe quem a fabricou.",
    "// MAC analisado. Spoofing tenta, banco de dados confirma.",
    # após hash/malware
    "// Hash verificado. Arquivos não mentem, só os que os carregam.",
    "// Assinatura consultada. O malware já esteve aqui antes.",
    "// VirusTotal consultado. Mais engines que desculpas encontradas.",
    # após domínio
    "// Domínio investigado. DNS é o cartório público da internet.",
    "// Reputação checada. Domínios jovens com score baixo: clássico.",
    "// WHOIS consultado. Privacidade de registro: o escudo favorito.",
    # genéricas
    "// Operação concluída. O alvo permanece inconsciente disso.",
    "// Processo finalizado. Inteligência coletada, dignidade preservada.",
    "// Etapa encerrada. Nem todo suspeito é culpado — só a maioria.",
    "// Dados salvos. O histórico é implacável com a memória curta.",
    "// Consulta encerrada. Transparência é boa — para quem observa.",
]

def _joke():
    """Retorna piada aleatória para o log. Porque leveza é uma virtude."""
    import random
    return random.choice(LOG_JOKES)


# ══════════════════════════════════════════════════════════════════════
#  MOTOR DE CONSULTA — onde a magia (leia-se: HTTP) acontece
# ══════════════════════════════════════════════════════════════════════

class ThreatEngine:
    """
    Motor de consulta defensiva a fontes públicas de inteligência.
    Não armazena nada localmente além de cache de sessão.
    // Porque privacidade é sagrada — exceto para quem abusa da internet.
    """

    ABUSEIPDB_KEY = ""   # configure sua chave em ~/.novacat/config.json
    VT_KEY        = ""   # VirusTotal — free tier disponível
    TIMEOUT       = 8    # segundos de paciência com servidores lentos

    def __init__(self, config_path: Path):
        # Carrega configuração se existir — sem chave, sem problema, usa fallback
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text())
                self.ABUSEIPDB_KEY = cfg.get("abuseipdb_key", "")
                self.VT_KEY        = cfg.get("virustotal_key", "")
            except Exception:
                pass  # configuração corrompida: fica pro usuário resolver

    def _get(self, url: str, headers: dict = None) -> dict | None:
        """
        GET HTTP básico sem dependências externas.
        // urllib: a navalha suíça de quem não quer instalar requests.
        """
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return {"_error": f"HTTP {e.code}", "_detail": str(e.reason)}
        except urllib.error.URLError as e:
            return {"_error": "Sem conexão", "_detail": str(e.reason)}
        except Exception as e:
            return {"_error": "Falha geral", "_detail": str(e)}

    # ── Validadores ──────────────────────────────────────────────────

    @staticmethod
    def is_ipv4(val: str) -> bool:
        """Valida IPv4. Simples mas eficaz — como a maioria dos ataques."""
        try:
            parts = val.strip().split(".")
            return len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts)
        except Exception:
            return False

    @staticmethod
    def is_ipv6(val: str) -> bool:
        """IPv6 — porque o mundo acabou com os IPv4 livres mas os ataques não."""
        try:
            socket.inet_pton(socket.AF_INET6, val.strip())
            return True
        except Exception:
            return False

    @staticmethod
    def is_mac(val: str) -> bool:
        """
        Valida endereço MAC em variados formatos.
        // AA:BB:CC:DD:EE:FF ou AA-BB-CC... o atacante escolhe o estilo.
        """
        clean = re.sub(r"[:\-\.]", "", val.strip())
        return len(clean) == 12 and all(c in "0123456789abcdefABCDEF" for c in clean)

    @staticmethod
    def is_hash(val: str) -> bool:
        """MD5/SHA1/SHA256/SHA512 — digital fingerprint que não mente."""
        v = val.strip()
        return len(v) in (32, 40, 64, 128) and all(
            c in "0123456789abcdefABCDEF" for c in v
        )

    @staticmethod
    def is_domain(val: str) -> bool:
        """Domínio? Checagem básica — DNS sabe mais."""
        return bool(re.match(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
            val.strip()
        ))

    @staticmethod
    def detect_type(val: str) -> str:
        """
        Detecta automaticamente o tipo do identificador.
        // O alvo não precisa saber que estamos identificando-o.
        """
        v = val.strip()
        if ThreatEngine.is_ipv4(v):   return "ipv4"
        if ThreatEngine.is_ipv6(v):   return "ipv6"
        if ThreatEngine.is_mac(v):    return "mac"
        if ThreatEngine.is_hash(v):   return "hash"
        if ThreatEngine.is_domain(v): return "domain"
        return "unknown"

    # ── Consultas ────────────────────────────────────────────────────

    def lookup_ip(self, ip: str, cb) -> dict:
        """
        Consulta IP em múltiplas fontes públicas.
        // Método favorito de quem acredita em segunda chance: verificar primeiro.
        """
        result = {"target": ip, "type": "ip", "sources": {}, "verdict": "DESCONHECIDO"}
        cb(f"[◈] Consultando geolocalização de {ip}…")

        # ip-api.com — gratuito, sem chave, generoso com os limites
        geo = self._get(f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields=66846719")
        if geo and "_error" not in geo:
            result["geo"] = {
                "pais":      geo.get("country", "—"),
                "regiao":    geo.get("regionName", "—"),
                "cidade":    geo.get("city", "—"),
                "isp":       geo.get("isp", "—"),
                "org":       geo.get("org", "—"),
                "asn":       geo.get("as", "—"),
                "lat":       geo.get("lat", 0),
                "lon":       geo.get("lon", 0),
                "proxy":     geo.get("proxy", False),
                "hosting":   geo.get("hosting", False),
                "vpn":       geo.get("vpn", False),
                "tor":       geo.get("tor", False),
            }
            cb(f"     País: {result['geo']['pais']} | ISP: {result['geo']['isp']}")
            cb(f"     ASN: {result['geo']['asn']}")
            flags = []
            if result["geo"]["proxy"]:   flags.append("PROXY")
            if result["geo"]["vpn"]:     flags.append("VPN")
            if result["geo"]["tor"]:     flags.append("TOR")
            if result["geo"]["hosting"]: flags.append("HOSTING")
            if flags:
                cb(f"     ⚡ Flags: {', '.join(flags)}")
                result["geo"]["flags"] = flags
        else:
            cb(f"     [!] Geolocalização indisponível: {(geo or {}).get('_detail','timeout')}")

        cb(_joke())

        # AbuseIPDB — exige chave mas tier gratuito é generoso
        if self.ABUSEIPDB_KEY:
            cb(f"[◈] Consultando AbuseIPDB…")
            abuse = self._get(
                f"https://api.abuseipdb.com/api/v2/check?ipAddress={urllib.parse.quote(ip)}&maxAgeInDays=90&verbose",
                headers={"Key": self.ABUSEIPDB_KEY, "Accept": "application/json"}
            )
            if abuse and "data" in abuse:
                d = abuse["data"]
                result["sources"]["abuseipdb"] = {
                    "score":      d.get("abuseConfidenceScore", 0),
                    "relatos":    d.get("totalReports", 0),
                    "ultimo":     d.get("lastReportedAt", "—"),
                    "categorias": d.get("reports", [])[:5],
                    "whitelist":  d.get("isWhitelisted", False),
                }
                score = d.get("abuseConfidenceScore", 0)
                cb(f"     Score AbuseIPDB: {score}/100 | Relatos: {d.get('totalReports',0)}")
                cb(_joke())
        else:
            cb("     [!] ABUSEIPDB_KEY não configurada — adicione em ~/.novacat/config.json")
            # fallback: AlienVault OTX público (sem chave necessária)
            cb(f"[◈] Consultando AlienVault OTX (público)…")
            otx = self._get(f"https://otx.alienvault.com/api/v1/indicators/IPv4/{urllib.parse.quote(ip)}/reputation")
            if otx and "_error" not in otx:
                rep = otx.get("reputation", {})
                result["sources"]["otx"] = {
                    "score":   rep.get("threat_score", 0),
                    "atividade": rep.get("activities", [])[:5],
                }
                cb(f"     OTX Threat Score: {rep.get('threat_score', 'N/D')}")
                cb(_joke())
            # fallback: ThreatFox
            cb(f"[◈] Consultando ThreatFox…")
            tf_payload = json.dumps({"query": "search_ioc", "search_term": ip}).encode()
            try:
                req = urllib.request.Request(
                    "https://threatfox-api.abuse.ch/api/v1/",
                    data=tf_payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                    tf = json.loads(r.read().decode())
                if tf.get("query_status") == "ok":
                    iocs = tf.get("data", [])
                    result["sources"]["threatfox"] = {
                        "encontrado": bool(iocs),
                        "iocs": iocs[:5],
                        "total": len(iocs),
                    }
                    if iocs:
                        cb(f"     ⚠ ThreatFox: {len(iocs)} IOC(s) encontrado(s)!")
                    else:
                        cb("     ThreatFox: sem registros para este IP.")
                    cb(_joke())
            except Exception as e:
                cb(f"     [!] ThreatFox: {e}")

        # Determina veredito consolidado
        result["verdict"] = self._verdict_ip(result)
        cb(f"[◈] Veredito: {result['verdict']}")
        return result

    def lookup_mac(self, mac: str, cb) -> dict:
        """
        Consulta fabricante de placa de rede via OUI.
        // Hardware tem identidade. MAC spoofing tenta disfarçar isso.
        """
        result = {"target": mac, "type": "mac", "sources": {}, "verdict": "DESCONHECIDO"}
        clean  = re.sub(r"[:\-\.]", "", mac.strip()).upper()
        oui    = ":".join([clean[i:i+2] for i in range(0, 6, 2)])

        cb(f"[◈] Consultando fabricante (OUI: {oui})…")
        # macvendors.com API pública
        vendor = self._get(f"https://api.macvendors.com/{urllib.parse.quote(oui)}")
        # esse endpoint retorna texto puro, não JSON
        try:
            req = urllib.request.Request(f"https://api.macvendors.com/{urllib.parse.quote(oui)}")
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                vendor_name = r.read().decode().strip()
        except Exception:
            vendor_name = "Fabricante desconhecido"

        result["vendor"] = vendor_name
        result["oui"]    = oui
        result["clean"]  = clean

        cb(f"     Fabricante: {vendor_name}")
        cb(f"     OUI: {oui} | MAC Completo: {clean}")

        # Verifica se parece ser um MAC broadcast/multicast
        first_byte = int(clean[:2], 16)
        is_multicast = bool(first_byte & 0x01)
        is_local     = bool(first_byte & 0x02)  # locally administered = possível spoofing
        result["multicast"] = is_multicast
        result["local_admin"] = is_local

        if is_multicast:
            cb("     ⚡ Flag: MULTICAST (endereço de grupo, não individual)")
        if is_local:
            cb("     ⚡ Flag: LOCALLY ADMINISTERED — possível MAC spoofing")
            # // Localmente administrado: o favorito de quem quer ser outra pessoa.

        cb(_joke())
        result["verdict"] = "SUSPEITO" if is_local else "LEGÍTIMO"
        cb(f"[◈] Veredito: {result['verdict']}")
        return result

    def lookup_hash(self, h: str, cb) -> dict:
        """
        Verifica hash contra bases públicas de malware.
        // SHA256 é o CPF do arquivo. E assim como CPF, às vezes aparece em listas negras.
        """
        result = {"target": h, "type": "hash", "sources": {}, "verdict": "DESCONHECIDO"}
        hlen   = len(h.strip())
        htype  = {32: "MD5", 40: "SHA1", 64: "SHA256", 128: "SHA512"}.get(hlen, "HASH")

        cb(f"[◈] Consultando {htype} no ThreatFox…")
        tf_payload = json.dumps({"query": "search_ioc", "search_term": h.strip()}).encode()
        try:
            req = urllib.request.Request(
                "https://threatfox-api.abuse.ch/api/v1/",
                data=tf_payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                tf = json.loads(r.read().decode())
            iocs = tf.get("data", []) if tf.get("query_status") == "ok" else []
            result["sources"]["threatfox"] = {
                "encontrado": bool(iocs),
                "iocs": iocs[:10],
                "total": len(iocs),
            }
            if iocs:
                malware = iocs[0].get("malware", "desconhecido")
                cb(f"     ⚠ ThreatFox: hash detectado! Malware: {malware}")
            else:
                cb("     ThreatFox: hash não encontrado em IOCs conhecidos.")
        except Exception as e:
            cb(f"     [!] ThreatFox: {e}")

        cb(_joke())

        # MalwareBazaar — outra gem da abuse.ch
        cb(f"[◈] Consultando MalwareBazaar…")
        try:
            mb_payload = urllib.parse.urlencode({"query": "get_info", "hash": h.strip()}).encode()
            req = urllib.request.Request(
                "https://mb-api.abuse.ch/api/v1/",
                data=mb_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                mb = json.loads(r.read().decode())
            if mb.get("query_status") == "ok":
                data = mb.get("data", [{}])[0]
                result["sources"]["malwarebazaar"] = {
                    "encontrado":  True,
                    "nome":        data.get("file_name", "—"),
                    "tipo":        data.get("file_type", "—"),
                    "familia":     data.get("signature", "—"),
                    "tags":        data.get("tags", []),
                    "primeiro":    data.get("first_seen", "—"),
                }
                cb(f"     ⚠ MalwareBazaar: {data.get('signature','desconhecido')} — {data.get('file_name','—')}")
                # // Arquivo fichado. Assim como o alvo, tem um histórico.
            else:
                result["sources"]["malwarebazaar"] = {"encontrado": False}
                cb("     MalwareBazaar: arquivo não catalogado.")
        except Exception as e:
            cb(f"     [!] MalwareBazaar: {e}")

        cb(_joke())

        # VirusTotal se tiver chave
        if self.VT_KEY:
            cb(f"[◈] Consultando VirusTotal…")
            vt = self._get(
                f"https://www.virustotal.com/api/v3/files/{h.strip()}",
                headers={"x-apikey": self.VT_KEY}
            )
            if vt and "data" in vt:
                stats = vt["data"]["attributes"].get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total     = sum(stats.values())
                result["sources"]["virustotal"] = {
                    "malicioso": malicious,
                    "total":     total,
                    "stats":     stats,
                }
                cb(f"     VT: {malicious}/{total} engines detectaram como malicioso")
                cb(_joke())

        result["verdict"] = self._verdict_hash(result)
        cb(f"[◈] Veredito: {result['verdict']}")
        return result

    def lookup_domain(self, domain: str, cb) -> dict:
        """
        Investiga reputação de domínio.
        // DNS é público. A privacidade de registro é o guarda-chuva favorito.
        """
        result = {"target": domain, "type": "domain", "sources": {}, "verdict": "DESCONHECIDO"}

        cb(f"[◈] Resolvendo DNS de {domain}…")
        try:
            ips = socket.getaddrinfo(domain.strip(), None)
            resolved = list({r[4][0] for r in ips})
            result["dns_resolved"] = resolved
            cb(f"     IPs resolvidos: {', '.join(resolved[:5])}")
        except Exception as e:
            result["dns_resolved"] = []
            cb(f"     [!] DNS falhou: {e}")

        cb(_joke())

        # URLhaus — para domínios usados em distribuição de malware
        cb(f"[◈] Consultando URLhaus…")
        try:
            uh_payload = urllib.parse.urlencode({"host": domain.strip()}).encode()
            req = urllib.request.Request(
                "https://urlhaus-api.abuse.ch/v1/host/",
                data=uh_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                uh = json.loads(r.read().decode())
            if uh.get("query_status") == "is_host":
                urls = uh.get("urls", [])
                result["sources"]["urlhaus"] = {
                    "encontrado": True,
                    "urls_total": len(urls),
                    "urls":       urls[:5],
                    "blacklists": uh.get("blacklists", {}),
                }
                cb(f"     ⚠ URLhaus: {len(urls)} URL(s) maliciosas detectadas!")
                cb(_joke())
            else:
                result["sources"]["urlhaus"] = {"encontrado": False}
                cb("     URLhaus: domínio não encontrado como host malicioso.")
        except Exception as e:
            cb(f"     [!] URLhaus: {e}")

        # ThreatFox lookup de domínio
        cb(f"[◈] Consultando ThreatFox…")
        try:
            tf_payload = json.dumps({"query": "search_ioc", "search_term": domain.strip()}).encode()
            req = urllib.request.Request(
                "https://threatfox-api.abuse.ch/api/v1/",
                data=tf_payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.TIMEOUT) as r:
                tf = json.loads(r.read().decode())
            iocs = tf.get("data", []) if tf.get("query_status") == "ok" else []
            result["sources"]["threatfox"] = {"encontrado": bool(iocs), "iocs": iocs[:5]}
            if iocs:
                cb(f"     ⚠ ThreatFox: {len(iocs)} IOC(s) ligado(s) ao domínio!")
            else:
                cb("     ThreatFox: domínio sem registros de C2/malware.")
            cb(_joke())
        except Exception as e:
            cb(f"     [!] ThreatFox: {e}")

        result["verdict"] = self._verdict_domain(result)
        cb(f"[◈] Veredito: {result['verdict']}")
        return result

    # ── Vereditos consolidados ────────────────────────────────────────

    def _verdict_ip(self, r: dict) -> str:
        """Score ponderado simples — sem ML, sem drama, sem desculpas."""
        score = 0
        geo   = r.get("geo", {})
        if geo.get("tor"):      score += 40
        if geo.get("proxy"):    score += 20
        if geo.get("vpn"):      score += 15
        if geo.get("hosting"):  score += 5
        abuse = r.get("sources", {}).get("abuseipdb", {})
        score += abuse.get("score", 0) * 0.4
        relatos = abuse.get("relatos", 0)
        if relatos > 50: score += 30
        elif relatos > 5: score += 10
        otx = r.get("sources", {}).get("otx", {})
        score += min(otx.get("score", 0), 30)
        tf = r.get("sources", {}).get("threatfox", {})
        if tf.get("encontrado"): score += 40

        if score >= 70:  return "MALICIOSO"
        if score >= 40:  return "SUSPEITO"
        if score >= 15:  return "OBSERVAR"
        return "LIMPO"

    def _verdict_hash(self, r: dict) -> str:
        """Hash encontrado em qualquer base = sinal vermelho."""
        if r["sources"].get("malwarebazaar", {}).get("encontrado"):  return "MALICIOSO"
        if r["sources"].get("threatfox",     {}).get("encontrado"):  return "MALICIOSO"
        vt = r["sources"].get("virustotal", {})
        if vt.get("malicioso", 0) > 3: return "MALICIOSO"
        if vt.get("malicioso", 0) > 0: return "SUSPEITO"
        return "LIMPO"

    def _verdict_domain(self, r: dict) -> str:
        """Domínio com URLhaus ou ThreatFox positivo? Não confie."""
        if r["sources"].get("urlhaus", {}).get("encontrado"):     return "MALICIOSO"
        if r["sources"].get("threatfox", {}).get("encontrado"):   return "MALICIOSO"
        return "LIMPO" if r.get("dns_resolved") else "DESCONHECIDO"


# ══════════════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA — Janela principal NovaCat
# ══════════════════════════════════════════════════════════════════════

class NovaCatApp(tk.Tk):
    """
    Interface principal do NovaCat.
    Frameless, transparente, arrastável, vermelha.
    // Porque ferramentas de segurança deveriam ter personalidade.
    """

    W, H = 1060, 740

    def __init__(self):
        super().__init__()

        # Configuração base da janela
        self.configure(bg=BG)
        self.overrideredirect(True)        # sem barra de título — somos discretos assim
        self.wm_attributes("-topmost", False)
        try:
            self.attributes("-alpha", 0.96)  # quase transparente, como as intenções do alvo
        except Exception:
            pass

        self._center()
        self.geometry(f"{self.W}x{self.H}")

        # Estado de arraste
        self._dx = self._dy = 0

        # Estado da consulta
        self._running   = False
        self._last_result = None

        # Itens animados
        self._glow_items  = []
        self._penta_items = []
        self._bg_pentas   = []
        self._eye_items   = []

        # Config
        self._cfg_path = Path.home() / ".novacat" / "config.json"
        self._cfg_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = ThreatEngine(self._cfg_path)

        self._build()
        self._animate_border()
        self._animate_eyes()
        self._animate_main_penta()
        self._animate_bg_pentas()

    def _center(self):
        """Centraliza a janela. O mínimo de cortesia que podemos oferecer."""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.W) // 2
        y  = (sh - self.H) // 2
        self.geometry(f"{self.W}x{self.H}+{x}+{y}")

    # ── Build principal ──────────────────────────────────────────────

    def _build(self):
        """Constrói toda a interface em um único Canvas + widgets."""
        self.cv = tk.Canvas(self, width=self.W, height=self.H,
                            bg=BG, highlightthickness=0)
        self.cv.pack(fill="both", expand=True)

        # Arrastar pela área do canvas
        self.cv.bind("<ButtonPress-1>",  self._press)
        self.cv.bind("<B1-Motion>",      self._drag)

        self._draw_background_pentas()  # pentagramas no fundo — decorativos
        self._draw_border()             # borda glow animada
        self._draw_cat_panel()          # painel lateral: gato + pentagrama principal
        self._draw_header()             # cabeçalho com título e botões
        self._draw_main_panel()         # painel principal: busca + resultados
        self._draw_log_bar()            # barra de log inferior

    def _draw_background_pentas(self):
        """
        Pentagramas de fundo — o wallpaper temático.
        // Estética é metade da intimidação.
        """
        c = self.cv
        positions = [
            (80, 80, 30), (200, 150, 20), (350, 60, 25),
            (500, 120, 18), (650, 70, 22), (780, 140, 28),
            (920, 80, 20), (60, 300, 18), (160, 400, 24),
            (300, 500, 20), (450, 350, 16), (600, 450, 22),
            (730, 320, 19), (860, 420, 25), (970, 350, 17),
            (100, 620, 21), (280, 680, 18), (500, 640, 23),
            (700, 660, 19), (900, 600, 26),
        ]
        for (px, py, pr) in positions:
            pts = [(px + pr * math.cos(math.radians(-90 + i * 144)),
                    py + pr * math.sin(math.radians(-90 + i * 144))) for i in range(5)]
            order = [0, 2, 4, 1, 3, 0]
            items = []
            # Círculo externo
            it = c.create_oval(px - pr - 4, py - pr - 4, px + pr + 4, py + pr + 4,
                                outline="#1a0505", width=1)
            items.append(it)
            for i in range(len(order) - 1):
                x1, y1 = pts[order[i]]
                x2, y2 = pts[order[i + 1]]
                it = c.create_line(x1, y1, x2, y2, fill="#1a0505", width=1)
                items.append(it)
            self._bg_pentas.append(items)

    def _draw_border(self):
        """Borda animada — o quadro da nossa pequena galeria de ameaças."""
        c = self.cv
        self._border_outer = c.create_rectangle(0, 0, self.W - 1, self.H - 1,
                                                  outline=GLOW1, width=2)
        self._border_inner = c.create_rectangle(3, 3, self.W - 4, self.H - 4,
                                                  outline=BORDER + "44", width=1)

    def _draw_cat_panel(self):
        """
        Painel lateral direito: gato de olhos vermelhos + pentagrama brilhante.
        // O gato sabe o que você fez na última requisição.
        """
        c   = self.cv
        PW  = 220   # largura do painel
        px  = self.W - PW

        # Fundo do painel
        c.create_rectangle(px, 1, self.W - 1, self.H - 1,
                            fill="#060202", outline=BORDER, width=1)
        c.create_line(px, 1, px, self.H - 1, fill=GLOW1, width=1)

        cx = px + PW // 2
        cy = 220  # centro vertical do gato

        # ── Corpo do gato (silhueta) ──────────────────────────────
        # Corpo oval
        c.create_oval(cx - 55, cy - 5, cx + 55, cy + 80,
                      fill="#0d0404", outline=GLOW1, width=1)

        # Cauda (curva decorativa)
        c.create_arc(cx + 30, cy + 30, cx + 90, cy + 100,
                     start=0, extent=200, outline=GLOW1, width=2, style="arc")

        # Cabeça
        c.create_oval(cx - 60, cy - 130, cx + 60, cy - 15,
                      fill="#110606", outline=GLOW1, width=1)

        # Orelhas — pontiagudas como as suspeitas
        c.create_polygon(cx - 60, cy - 85, cx - 85, cy - 165, cx - 25, cy - 105,
                         fill="#1a0808", outline=GLOW1, width=1)
        c.create_polygon(cx + 60, cy - 85, cx + 85, cy - 165, cx + 25, cy - 105,
                         fill="#1a0808", outline=GLOW1, width=1)
        # Interior das orelhas
        c.create_polygon(cx - 58, cy - 87, cx - 75, cy - 148, cx - 28, cy - 108,
                         fill=BORDER + "55")
        c.create_polygon(cx + 58, cy - 87, cx + 75, cy - 148, cx + 28, cy - 108,
                         fill=BORDER + "55")

        # ── Olhos vermelhos animados ──────────────────────────────
        for ex in [cx - 22, cx + 22]:
            # Sclera escura
            it = c.create_oval(ex - 14, cy - 78, ex + 14, cy - 48,
                                fill="#1a0000", outline=GLOW1, width=1)
            self._eye_items.append(("bg", it))
            # Íris vermelha
            it = c.create_oval(ex - 10, cy - 75, ex + 10, cy - 51,
                                fill=GLOW1, outline="")
            self._eye_items.append(("iris", it))
            # Pupila
            it = c.create_oval(ex - 5, cy - 72, ex + 5, cy - 54,
                                fill="#000000", outline="")
            self._eye_items.append(("pupil", it))
            # Brilho
            it = c.create_oval(ex - 8, cy - 74, ex - 3, cy - 68,
                                fill=GLOW3, outline="")
            self._eye_items.append(("glow", it))

        # Nariz
        c.create_polygon(cx - 5, cy - 35, cx + 5, cy - 35, cx, cy - 27,
                         fill=BORDER)
        # Boca
        c.create_line(cx, cy - 27, cx - 8, cy - 18, fill=BORDER, width=1)
        c.create_line(cx, cy - 27, cx + 8, cy - 18, fill=BORDER, width=1)

        # Bigodes — porque detalhes importam
        for dy in [-6, -2, 2]:
            c.create_line(cx - 55, cy - 35 + dy, cx - 12, cy - 35 + dy,
                          fill=BORDER, width=1)
            c.create_line(cx + 12, cy - 35 + dy, cx + 55, cy - 35 + dy,
                          fill=BORDER, width=1)

        # ── Pentagrama principal brilhante ────────────────────────
        pcy = cy + 175
        pr  = 48
        # Círculo externo do pentagrama
        c.create_oval(cx - pr - 8, pcy - pr - 8, cx + pr + 8, pcy + pr + 8,
                      outline=GLOW1, width=2)
        c.create_oval(cx - pr - 12, pcy - pr - 12, cx + pr + 12, pcy + pr + 12,
                      outline=BORDER + "66", width=1)

        pts = [(cx + pr * math.cos(math.radians(-90 + i * 144)),
                pcy + pr * math.sin(math.radians(-90 + i * 144))) for i in range(5)]
        order = [0, 2, 4, 1, 3, 0]
        for i in range(len(order) - 1):
            x1, y1 = pts[order[i]]
            x2, y2 = pts[order[i + 1]]
            it = c.create_line(x1, y1, x2, y2, fill=GLOW1, width=2)
            self._penta_items.append(it)

        for px2, py2 in pts:
            it = c.create_oval(px2 - 4, py2 - 4, px2 + 4, py2 + 4,
                                fill=GLOW2, outline=GLOW3)
            self._penta_items.append(it)

        # Centro brilhante
        it = c.create_text(cx, pcy, text="✦", font=("Courier New", 14, "bold"),
                            fill=GLOW2)
        self._penta_items.append(it)

        # Texto decorativo no painel
        c.create_text(cx, cy + 135, text="◈ THREAT INTEL ◈",
                      font=("Courier New", 8, "bold"), fill=MUTED)
        c.create_text(cx, pcy + 68, text="// VELVET DAGGER",
                      font=("Courier New", 7), fill=DIM)
        c.create_text(cx, pcy + 82, text=f"v{VERSION}",
                      font=("Courier New", 7), fill=DIM)

        # Pequenos pentagramas decorativos abaixo do principal
        for i, (spx, spy, spr) in enumerate([
            (cx - 55, pcy + 52, 12),
            (cx,      pcy + 62, 10),
            (cx + 55, pcy + 52, 12),
        ]):
            spts = [(spx + spr * math.cos(math.radians(-90 + j * 144)),
                     spy + spr * math.sin(math.radians(-90 + j * 144))) for j in range(5)]
            sord = [0, 2, 4, 1, 3, 0]
            for k in range(len(sord) - 1):
                x1, y1 = spts[sord[k]]
                x2, y2 = spts[sord[k + 1]]
                c.create_line(x1, y1, x2, y2, fill=BORDER, width=1)

    def _draw_header(self):
        """Cabeçalho com título, versão e controles de janela."""
        c = self.cv
        PW = 220
        # Fundo do header
        c.create_rectangle(0, 0, self.W - PW, 52, fill=BG2, outline="")
        c.create_line(0, 52, self.W - PW, 52, fill=GLOW1, width=1)

        # Ícone + título
        c.create_text(18, 26, text="◈", font=("Courier New", 18, "bold"),
                      fill=GLOW2, anchor="w")
        c.create_text(48, 16, text=f"{NAME}",
                      font=("Courier New", 15, "bold"), fill=TEXT, anchor="w")
        c.create_text(48, 34, text=f"v{VERSION}  ·  {CODENAME}  ·  Defensive Threat Intelligence",
                      font=("Courier New", 8), fill=MUTED, anchor="w")

        # Botões de controle
        btn_x = self.W - PW - 20
        close  = c.create_text(btn_x,      26, text="✕", font=("Courier New", 13, "bold"), fill=MUTED)
        mini   = c.create_text(btn_x - 30, 26, text="−", font=("Courier New", 13, "bold"), fill=MUTED)

        def on_close(e): self.destroy()
        def on_mini(e):  self.iconify()

        for btn, fn, col_h in [(close, on_close, GLOW1), (mini, on_mini, GLOW3)]:
            c.tag_bind(btn, "<Enter>",   lambda e, b=btn, col=col_h: c.itemconfigure(b, fill=col))
            c.tag_bind(btn, "<Leave>",   lambda e, b=btn: c.itemconfigure(b, fill=MUTED))
            c.tag_bind(btn, "<Button-1>", fn)

    def _draw_main_panel(self):
        """
        Painel principal: campo de busca, seletor de tipo,
        área de resultados e estatísticas.
        // Onde a inteligência acontece. Ou tentativa dela.
        """
        c   = self.cv
        PW  = 220
        MW  = self.W - PW  # largura útil

        # ── Campo de busca ────────────────────────────────────────
        c.create_text(18, 68, text="ALVO  (IP · MAC · Hash · Domínio · Identificador de NIC)",
                      font=("Courier New", 9, "bold"), fill=GLOW2, anchor="w")

        # Frame de entrada
        self._entry_frame = tk.Frame(self, bg=BG3, bd=0)
        self._entry_frame.place(x=16, y=82, width=MW - 160, height=34)
        self._entry = tk.Entry(self._entry_frame,
                               bg="#100505", fg=GLOW3,
                               insertbackground=GLOW2,
                               font=("Courier New", 11),
                               relief="flat", bd=4,
                               selectbackground=BORDER,
                               selectforeground=TEXT)
        self._entry.pack(fill="both", expand=True)
        self._entry.bind("<Return>", lambda e: self._start_lookup())
        c.create_rectangle(15, 81, MW - 145, 117, outline=BORDER, width=1)

        # Botão scan
        self._btn_scan = tk.Button(self,
            text="▶ SCAN",
            font=("Courier New", 11, "bold"),
            bg=GLOW1, fg="#fff",
            activebackground=BORDER, activeforeground="#fff",
            relief="flat", bd=0, cursor="hand2",
            command=self._start_lookup)
        self._btn_scan.place(x=MW - 142, y=82, width=120, height=34)

        # Botão limpar
        self._btn_clear = tk.Button(self,
            text="✕ LIMPAR",
            font=("Courier New", 9),
            bg=BG3, fg=MUTED,
            activebackground=BG4, activeforeground=TEXT,
            relief="flat", bd=0, cursor="hand2",
            command=self._clear)
        self._btn_clear.place(x=MW - 18, y=82, width=18, height=34)

        # ── Indicadores de tipo ───────────────────────────────────
        types_y = 125
        c.create_text(18, types_y, text="TIPO DETECTADO:",
                      font=("Courier New", 8), fill=MUTED, anchor="w")

        type_labels = ["IPv4", "IPv6", "MAC", "HASH", "DOMÍNIO", "AUTO"]
        self._type_lbl_items = {}
        for i, t in enumerate(type_labels):
            tx = 130 + i * 100
            it = c.create_text(tx, types_y, text=f"[ {t} ]",
                                font=("Courier New", 8), fill=DIM, anchor="w")
            self._type_lbl_items[t] = it

        # ── Área de resultado ─────────────────────────────────────
        res_y = 140
        c.create_line(16, res_y, MW - 16, res_y, fill=BORDER + "55", width=1)

        # Score / veredito principal
        c.create_text(18, res_y + 14, text="VEREDITO",
                      font=("Courier New", 9, "bold"), fill=MUTED, anchor="w")
        self._verdict_text = c.create_text(100, res_y + 14, text="—",
                                            font=("Courier New", 14, "bold"),
                                            fill=DIM, anchor="w")

        # Barra de score visual
        c.create_rectangle(200, res_y + 6, 550, res_y + 22,
                            fill="#100404", outline=BORDER, width=1)
        self._score_bar = c.create_rectangle(200, res_y + 6, 200, res_y + 22,
                                              fill=GLOW1, outline="")
        self._score_text = c.create_text(555, res_y + 14, text="0%",
                                          font=("Courier New", 9), fill=MUTED, anchor="w")

        # Área de detalhes — Text widget
        detail_y = res_y + 30
        detail_h = self.H - detail_y - 80  # reserva 80px para o log

        self._detail_frame = tk.Frame(self, bg=BG3)
        self._detail_frame.place(x=16, y=detail_y, width=MW - 30, height=detail_h)

        self._detail_txt = tk.Text(
            self._detail_frame,
            bg="#080202", fg=TEXT,
            font=("Courier New", 9),
            relief="flat", bd=0,
            state="disabled", wrap="word",
            selectbackground=BORDER,
        )
        # Tags de cor para o widget de texto
        self._detail_txt.tag_configure("title",   foreground=GLOW2,   font=("Courier New", 9, "bold"))
        self._detail_txt.tag_configure("key",     foreground=GLOW3,   font=("Courier New", 9))
        self._detail_txt.tag_configure("val",     foreground=TEXT)
        self._detail_txt.tag_configure("danger",  foreground=DANGER,  font=("Courier New", 9, "bold"))
        self._detail_txt.tag_configure("warn",    foreground=WARNING)
        self._detail_txt.tag_configure("ok",      foreground=SUCCESS)
        self._detail_txt.tag_configure("info",    foreground=INFO)
        self._detail_txt.tag_configure("muted",   foreground=MUTED)
        self._detail_txt.tag_configure("dim",     foreground=DIM)
        self._detail_txt.tag_configure("sep",     foreground=BORDER)

        sb = tk.Scrollbar(self._detail_frame, orient="vertical",
                          command=self._detail_txt.yview,
                          bg=BG, troughcolor=BG, activebackground=GLOW1,
                          relief="flat", bd=0)
        self._detail_txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._detail_txt.pack(fill="both", expand=True)
        c.create_rectangle(15, detail_y - 1, MW - 15, detail_y + detail_h + 1,
                            outline=BORDER, width=1)

        # Mensagem de boas-vindas
        self._show_welcome()

    def _draw_log_bar(self):
        """
        Barra de log inferior — onde as piadas e os processos coexistem.
        // O log mais honesto da ferramenta.
        """
        c    = self.cv
        PW   = 220
        MW   = self.W - PW
        LH   = 70   # altura da log bar
        ly   = self.H - LH

        c.create_rectangle(0, ly, MW, self.H, fill=BG2, outline="")
        c.create_line(0, ly, MW, ly, fill=GLOW1, width=1)

        c.create_text(14, ly + 10, text="▌ LOG",
                      font=("Courier New", 8, "bold"), fill=GLOW1, anchor="w")

        # Text widget inline na log bar
        self._log_frame = tk.Frame(self, bg=BG2)
        self._log_frame.place(x=60, y=ly + 3, width=MW - 74, height=LH - 6)

        self._log_txt = tk.Text(
            self._log_frame,
            bg="#060101", fg=MONO,
            font=("Courier New", 8),
            relief="flat", bd=0,
            state="disabled", wrap="word",
        )
        sb_log = tk.Scrollbar(self._log_frame, orient="vertical",
                               command=self._log_txt.yview,
                               bg=BG2, troughcolor=BG2, activebackground=GLOW1,
                               relief="flat", bd=0)
        self._log_txt.configure(yscrollcommand=sb_log.set)
        sb_log.pack(side="right", fill="y")
        self._log_txt.pack(fill="both", expand=True)

        # Timestamp
        self._ts_item = c.create_text(MW - 10, ly + LH - 8,
                                       text="", font=("Courier New", 7),
                                       fill=DIM, anchor="e")
        self._update_ts()

    # ── Animações ────────────────────────────────────────────────────

    def _animate_border(self):
        """Borda pulsante — porque tudo aqui tem vida."""
        colors = [GLOW1, "#d42020", "#dc2626", "#e03030", "#dc2626",
                  GLOW1, "#b01010", "#980d0d", "#b01010", GLOW1]
        idx = [0]
        def tick():
            if not self.winfo_exists(): return
            col = colors[idx[0] % len(colors)]
            self.cv.itemconfigure(self._border_outer, outline=col)
            idx[0] += 1
            self.after(110, tick)
        tick()

    def _animate_eyes(self):
        """Olhos que pulsam em vermelho. Não, eles não estão te julgando."""
        reds = [GLOW1, "#d42020", GLOW2, "#ff4444", GLOW2, GLOW1,
                "#b01010", "#980d0d", GLOW1]
        gls  = [GLOW3, GLOW4, "#ffbbbb", GLOW3, GLOW2, GLOW3]
        idx  = [0]
        def tick():
            if not self.winfo_exists(): return
            c   = self.cv
            col = reds[idx[0] % len(reds)]
            gcol= gls[idx[0] % len(gls)]
            for kind, it in self._eye_items:
                try:
                    if kind == "iris": c.itemconfigure(it, fill=col)
                    if kind == "glow": c.itemconfigure(it, fill=gcol)
                except Exception:
                    pass
            idx[0] += 1
            self.after(150, tick)
        tick()

    def _animate_main_penta(self):
        """Pentagrama principal com glow vermelho pulsante."""
        reds = ["#8b0000","#a01010", GLOW1, "#dc2626", GLOW2,
                "#dc2626", GLOW1, "#a01010","#8b0000"]
        idx  = [0]
        def tick():
            if not self.winfo_exists(): return
            col = reds[idx[0] % len(reds)]
            for it in self._penta_items:
                try:
                    self.cv.itemconfigure(it, fill=col, outline=col)
                except Exception:
                    pass
            idx[0] += 1
            self.after(140, tick)
        tick()

    def _animate_bg_pentas(self):
        """Pentagramas de fundo respiram levemente — muito levemente."""
        phase = [0]
        bg_cols = ["#0e0303","#120404","#160505","#120404","#0e0303","#0a0202"]
        def tick():
            if not self.winfo_exists(): return
            col = bg_cols[phase[0] % len(bg_cols)]
            for items in self._bg_pentas:
                for it in items:
                    try:
                        self.cv.itemconfigure(it, fill=col, outline=col)
                    except Exception:
                        pass
            phase[0] += 1
            self.after(400, tick)
        tick()

    def _update_ts(self):
        """Timestamp no canto do log — o tempo não perdoa."""
        try:
            ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            self.cv.itemconfigure(self._ts_item, text=ts)
        except Exception:
            pass
        self.after(1000, self._update_ts)

    # ── Controle de janela ───────────────────────────────────────────

    def _press(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self._dx}"
                      f"+{self.winfo_y() + e.y - self._dy}")

    # ── Log ──────────────────────────────────────────────────────────

    def _log(self, msg: str):
        """Adiciona linha ao log inferior. Thread-safe."""
        def _do():
            self._log_txt.configure(state="normal")
            self._log_txt.insert("end", msg + "\n")
            self._log_txt.see("end")
            self._log_txt.configure(state="disabled")
        try:
            self._log_txt.after(0, _do)
        except Exception:
            pass

    def _detail_clear(self):
        """Limpa área de detalhes."""
        self._detail_txt.configure(state="normal")
        self._detail_txt.delete("1.0", "end")
        self._detail_txt.configure(state="disabled")

    def _detail_write(self, text: str, tag: str = "val"):
        """Escreve na área de detalhes com colorização."""
        self._detail_txt.configure(state="normal")
        self._detail_txt.insert("end", text, tag)
        self._detail_txt.configure(state="disabled")
        self._detail_txt.see("end")

    def _dln(self, key: str, val: str, key_tag="key", val_tag="val"):
        """Linha de detalhe formatada: chave + valor."""
        self._detail_write(f"  {key:<24}", key_tag)
        self._detail_write(f"{val}\n", val_tag)

    def _dsep(self, title: str = ""):
        """Separador de seção na área de detalhes."""
        if title:
            line = f"\n  ─── {title} {'─' * max(0, 44 - len(title))}\n"
        else:
            line = f"\n  {'─' * 50}\n"
        self._detail_write(line, "sep")

    # ── Lookup ───────────────────────────────────────────────────────

    def _start_lookup(self):
        """Inicia consulta em thread separada. O UI não pode ser bloqueado."""
        if self._running:
            self._log("// Uma consulta já está em andamento. Paciência é virtude.")
            return

        val = self._entry.get().strip()
        if not val:
            self._log("// Campo vazio. O nada não tem histórico — ainda.")
            return

        dtype = ThreatEngine.detect_type(val)

        # Destaca tipo detectado
        for t, it in self._type_lbl_items.items():
            col = GLOW2 if t.lower() in dtype.lower() or (t == "AUTO" and dtype != "unknown") \
                else DIM
            self.cv.itemconfigure(it, fill=col)

        if dtype == "unknown":
            self._log(f"// Tipo não reconhecido: '{val[:30]}' — IP, MAC, hash ou domínio, por favor.")
            return

        self._running = True
        self._btn_scan.configure(state="disabled", text="…")
        self._detail_clear()
        self._set_verdict("CONSULTANDO…", 0, INFO)
        self._log(f"[>>] Iniciando consulta: {val} ({dtype.upper()})")

        def task():
            try:
                if   dtype in ("ipv4", "ipv6"): r = self.engine.lookup_ip(val, self._log)
                elif dtype == "mac":             r = self.engine.lookup_mac(val, self._log)
                elif dtype == "hash":            r = self.engine.lookup_hash(val, self._log)
                elif dtype == "domain":          r = self.engine.lookup_domain(val, self._log)
                else:                            r = {"verdict": "DESCONHECIDO", "type": dtype}
                self._last_result = r
                self.after(0, lambda: self._render_result(r))
            except Exception as ex:
                self._log(f"[!!] Erro inesperado: {ex}")
                # // Erros inesperados: a versão digital do dia que não devia ter começado.
            finally:
                self._running = False
                self.after(0, lambda: self._btn_scan.configure(state="normal", text="▶ SCAN"))

        threading.Thread(target=task, daemon=True).start()

    def _render_result(self, r: dict):
        """Renderiza resultado completo na área de detalhes."""
        verdict = r.get("verdict", "DESCONHECIDO")
        dtype   = r.get("type", "—")
        target  = r.get("target", "—")

        # Cor do veredito
        vcol = {
            "MALICIOSO":     DANGER,
            "SUSPEITO":      WARNING,
            "OBSERVAR":      "#f59e0b",
            "LIMPO":         SUCCESS,
            "DESCONHECIDO":  MUTED,
            "LEGÍTIMO":      SUCCESS,
        }.get(verdict, MUTED)

        score_pct = {
            "MALICIOSO": 90, "SUSPEITO": 60, "OBSERVAR": 35,
            "LIMPO": 5, "LEGÍTIMO": 5, "DESCONHECIDO": 0,
        }.get(verdict, 0)

        self._set_verdict(verdict, score_pct, vcol)
        self._detail_clear()

        # Cabeçalho
        self._detail_write(f"\n  ◈  RELATÓRIO DE INTELIGÊNCIA — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "title")
        self._dsep()
        self._dln("Alvo:",     target)
        self._dln("Tipo:",     dtype.upper())
        self._dln("Veredito:", verdict, val_tag=("danger" if verdict == "MALICIOSO" else
                                                  "warn"   if verdict == "SUSPEITO"  else
                                                  "ok"     if verdict in ("LIMPO","LEGÍTIMO") else "muted"))

        # Seções por tipo
        if dtype in ("ipv4", "ipv6"):
            self._render_ip(r)
        elif dtype == "mac":
            self._render_mac(r)
        elif dtype == "hash":
            self._render_hash(r)
        elif dtype == "domain":
            self._render_domain(r)

        self._dsep()
        self._detail_write(f"\n  // Consulta realizada em {datetime.now().strftime('%H:%M:%S')}. ", "dim")
        self._detail_write("Dados de fontes públicas, sem garantia de completude.\n", "dim")
        self._log(f"[✓] Relatório gerado: {target} → {verdict}")
        self._log(_joke())

    def _render_ip(self, r: dict):
        """Seção de detalhes para IPs."""
        geo = r.get("geo", {})
        if geo:
            self._dsep("GEOLOCALIZAÇÃO")
            self._dln("País:",    geo.get("pais", "—"))
            self._dln("Região:",  geo.get("regiao", "—"))
            self._dln("Cidade:",  geo.get("cidade", "—"))
            self._dln("ISP:",     geo.get("isp", "—"))
            self._dln("Org:",     geo.get("org", "—"))
            self._dln("ASN:",     geo.get("asn", "—"))
            flags = geo.get("flags", [])
            if flags:
                self._detail_write(f"\n  ⚡ Flags detectadas: ", "key")
                self._detail_write(", ".join(flags) + "\n", "danger")

        abuse = r.get("sources", {}).get("abuseipdb", {})
        if abuse:
            self._dsep("ABUSEIPDB")
            score = abuse.get("score", 0)
            stag  = "danger" if score >= 70 else "warn" if score >= 30 else "ok"
            self._dln("Score:",   f"{score}/100", val_tag=stag)
            self._dln("Relatos:", str(abuse.get("relatos", 0)))
            self._dln("Último:",  str(abuse.get("ultimo", "—")))

        otx = r.get("sources", {}).get("otx", {})
        if otx:
            self._dsep("ALIENVAULT OTX")
            self._dln("Threat Score:", str(otx.get("score", "—")))

        tf = r.get("sources", {}).get("threatfox", {})
        if tf:
            self._dsep("THREATFOX")
            found = tf.get("encontrado", False)
            self._dln("Detectado:", "SIM ⚠" if found else "Não", val_tag="danger" if found else "ok")
            if found:
                self._dln("IOCs:", str(tf.get("total", 0)))
                for ioc in tf.get("iocs", [])[:3]:
                    self._detail_write(f"    → {ioc.get('ioc_value','—')} "
                                        f"[{ioc.get('malware','—')}]\n", "warn")

    def _render_mac(self, r: dict):
        """Seção de detalhes para MACs."""
        self._dsep("INFORMAÇÕES DO DISPOSITIVO")
        self._dln("Fabricante:", r.get("vendor", "—"))
        self._dln("OUI:",        r.get("oui", "—"))
        self._dln("MAC Limpo:",  r.get("clean", "—"))
        self._dln("Multicast:",  "SIM" if r.get("multicast") else "Não")
        la = r.get("local_admin", False)
        self._dln("Locally Adm.:", ("SIM ⚡ — possível spoofing" if la else "Não"),
                  val_tag="warn" if la else "ok")

    def _render_hash(self, r: dict):
        """Seção de detalhes para hashes."""
        mb = r.get("sources", {}).get("malwarebazaar", {})
        if mb.get("encontrado"):
            self._dsep("MALWAREBAZAAR")
            self._dln("Nome:",    mb.get("nome", "—"))
            self._dln("Tipo:",    mb.get("tipo", "—"))
            self._dln("Família:", mb.get("familia", "—"), val_tag="danger")
            self._dln("Tags:",    ", ".join(mb.get("tags", [])))
            self._dln("Visto em:", mb.get("primeiro", "—"))

        tf = r.get("sources", {}).get("threatfox", {})
        if tf:
            self._dsep("THREATFOX")
            found = tf.get("encontrado", False)
            self._dln("Detectado:", "SIM ⚠" if found else "Não", val_tag="danger" if found else "ok")
            for ioc in tf.get("iocs", [])[:3]:
                self._detail_write(f"    → {ioc.get('malware','—')} "
                                    f"[{ioc.get('ioc_type','—')}]\n", "warn")

        vt = r.get("sources", {}).get("virustotal", {})
        if vt:
            self._dsep("VIRUSTOTAL")
            mal   = vt.get("malicioso", 0)
            total = vt.get("total", 0)
            vtag  = "danger" if mal > 3 else "warn" if mal > 0 else "ok"
            self._dln("Detecções:", f"{mal}/{total}", val_tag=vtag)

    def _render_domain(self, r: dict):
        """Seção de detalhes para domínios."""
        ips = r.get("dns_resolved", [])
        self._dsep("DNS")
        self._dln("IPs resolvidos:", ", ".join(ips) if ips else "Não resolvido",
                  val_tag="val" if ips else "warn")

        uh = r.get("sources", {}).get("urlhaus", {})
        if uh:
            self._dsep("URLHAUS")
            found = uh.get("encontrado", False)
            self._dln("Detectado:", "SIM ⚠" if found else "Não", val_tag="danger" if found else "ok")
            if found:
                self._dln("URLs:", str(uh.get("urls_total", 0)))
                for u in uh.get("urls", [])[:3]:
                    self._detail_write(f"    → {u.get('url','—')[:70]}\n", "warn")

        tf = r.get("sources", {}).get("threatfox", {})
        if tf:
            self._dsep("THREATFOX")
            found = tf.get("encontrado", False)
            self._dln("Detectado:", "SIM ⚠" if found else "Não", val_tag="danger" if found else "ok")

    def _set_verdict(self, text: str, pct: int, color: str):
        """Atualiza o veredito e a barra de score visual."""
        PW = 220
        MW = self.W - PW
        self.cv.itemconfigure(self._verdict_text, text=text, fill=color)
        bar_w = int(pct / 100 * 350)
        self.cv.coords(self._score_bar, 200, 154, 200 + bar_w, 170)
        self.cv.itemconfigure(self._score_bar, fill=color)
        self.cv.itemconfigure(self._score_text, text=f"{pct}%")

    def _clear(self):
        """Limpa tudo — fresh start para o próximo alvo suspeito."""
        self._entry.delete(0, "end")
        self._detail_clear()
        self._set_verdict("—", 0, DIM)
        for it in self._type_lbl_items.values():
            self.cv.itemconfigure(it, fill=DIM)
        self._show_welcome()
        self._log("// Tudo limpo. Próximo alvo, por favor.")

    def _show_welcome(self):
        """Mensagem de boas-vindas na área de detalhes."""
        self._detail_clear()
        self._detail_write("\n\n", "val")
        self._detail_write("  ◈  BEM-VINDO AO NOVACAT  —  VELVET DAGGER\n\n", "title")
        self._detail_write("  Ferramenta defensiva de Cyber Threat Intelligence.\n", "muted")
        self._detail_write("  Consulta histórico público de identificadores de rede.\n\n", "muted")
        self._detail_write("  IDENTIFICADORES SUPORTADOS:\n", "key")
        items = [
            ("  IPv4 / IPv6", "ex: 1.2.3.4 · 2001:db8::1"),
            ("  MAC Address",  "ex: AA:BB:CC:DD:EE:FF"),
            ("  Hash MD5/SHA", "ex: d41d8cd98f00b204e9800998ecf8427e"),
            ("  Domínio",      "ex: suspeito.example.com"),
        ]
        for k, v in items:
            self._detail_write(f"\n  {k:<22}", "key")
            self._detail_write(f"  {v}", "dim")

        self._detail_write("\n\n  FONTES CONSULTADAS:\n", "key")
        sources = ["ip-api.com", "AbuseIPDB*", "AlienVault OTX", "ThreatFox",
                   "MalwareBazaar", "URLhaus", "MACVendors", "VirusTotal*"]
        self._detail_write("  " + "  ·  ".join(sources) + "\n", "muted")
        self._detail_write("\n  * Requer chave API (gratuita) em ~/.novacat/config.json\n", "dim")
        self._detail_write("\n  // Insira o identificador acima e pressione SCAN.\n", "dim")
        self._detail_write("  // O histórico não esquece. Você sim.\n", "dim")


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def main():
    """
    Ponto de entrada do NovaCat.
    // Aqui começa o monitoramento. Ou a consciência culpada do alvo.
    """
    # Verifica Python mínimo — porque retrocompatibilidade tem limites
    if sys.version_info < (3, 8):
        print(f"[!] Python 3.8+ necessário. Atual: {sys.version}")
        sys.exit(1)

    # Cria config padrão se não existir
    cfg = Path.home() / ".novacat" / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.exists():
        cfg.write_text(json.dumps({
            "abuseipdb_key": "",
            "virustotal_key": "",
            "theme": "crimson",
            "comment": "Adicione suas chaves API gratuitas aqui."
        }, indent=2))

    app = NovaCatApp()
    app.title(f"{NAME} {VERSION}")
    app.mainloop()


if __name__ == "__main__":
    main()
