#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   NovaCat  v1.0.0  —  VELVET DAGGER                                 ║
║   Installer · Frameless · Transparent · Red Glow                    ║
║   "Instala silencioso. Como o alvo deveria ter sido."               ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os, sys, subprocess, threading, shutil, time, math
from pathlib import Path

try:
    import tkinter as tk
except ImportError:
    print("[!] tkinter ausente.")
    print("    Arch:   sudo pacman -S tk")
    print("    Debian: sudo apt install python3-tk")
    sys.exit(1)

# ── Paleta — o mesmo vermelho de sempre, porque consistência importa ─
BG      = "#050303"
BG2     = "#090404"
BG3     = "#100606"
GLOW1   = "#cc1a1a"
GLOW2   = "#ff3333"
GLOW3   = "#ff6060"
BORDER  = "#8b0000"
TEXT    = "#f2e0e0"
MUTED   = "#7a5050"
DIM     = "#4a3030"
SUCCESS = "#22c55e"
DANGER  = "#ef4444"
WARNING = "#f59e0b"
MONO    = "#ff8888"

VERSION  = "1.0.0"
NAME     = "NovaCat"
CODENAME = "VELVET DAGGER"

INSTALL_DIR  = Path.home() / ".local" / "share" / "novacat"
BIN_DIR      = Path.home() / ".local" / "bin"
CONFIG_DIR   = Path.home() / ".novacat"
DESKTOP_FILE = Path.home() / ".local" / "share" / "applications" / "novacat.desktop"
MAIN_SCRIPT  = "NovaCat.py"

# ── Piadas do log de instalação — porque instalar também pode ser divertido ─
INSTALL_JOKES = [
    "// pip instalou sem reclamar. Raro como inocência nesse negócio.",
    "// Dependências resolvidas. O alvo não vai ter a mesma sorte.",
    "// Arquivo copiado. Discriçã? Nunca ouvi falar.",
    "// Launcher criado. Acesso em um comando — irônico, não é?",
    "// .desktop entry criada. Integração ao sistema: completa.",
    "// Verificação concluída. Ferramentas presentes, desculpas ausentes.",
    "// Configuração padrão criada. Personalize sem dramas.",
    "// Tudo instalado. O alvo continua sem saber.",
]

def _joke():
    import random
    return random.choice(INSTALL_JOKES)


def run_cmd(cmd, timeout=90):
    """Executa comando shell. // Se falhar, pelo menos falhou em silêncio."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def do_install(log_cb, prog_cb, done_cb):
    """
    Rotina de instalação executada em thread.
    // Sequencial, determinístico, sem surpresas — o oposto do alvo.
    """
    errors = []

    def step(pct, msg, fn=None):
        log_cb(f"[>>] {msg}")
        if fn:
            ok, out = fn()
            if not ok:
                log_cb(f"[!!] {out[:120] if out else 'Falhou'}")
                errors.append(msg)
            else:
                if out:
                    log_cb(f"     {out[:80]}")
        prog_cb(pct, msg)
        time.sleep(0.4)

    # ── Verificações iniciais ─────────────────────────────────────
    step(5, "Verificando Python 3.8+",
         lambda: (sys.version_info >= (3, 8), sys.version))

    step(15, "Instalando psutil",
         lambda: run_cmd(f"{sys.executable} -m pip install psutil --quiet --break-system-packages"
                         if _is_arch() else
                         f"{sys.executable} -m pip install psutil --quiet"))
    log_cb(_joke())

    step(28, "Instalando Pillow",
         lambda: run_cmd(f"{sys.executable} -m pip install Pillow --quiet --break-system-packages"
                         if _is_arch() else
                         f"{sys.executable} -m pip install Pillow --quiet"))
    log_cb(_joke())

    step(38, "Verificando tkinter",
         lambda: (True, f"tkinter OK — versão {tk.TkVersion}"))

    # ── Cria diretórios ───────────────────────────────────────────
    log_cb("[>>] Criando diretórios de instalação…")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    prog_cb(48, "Diretórios criados")
    time.sleep(0.3)

    # ── Copia script principal ────────────────────────────────────
    log_cb("[>>] Copiando NovaCat.py…")
    src = Path(__file__).parent / MAIN_SCRIPT
    if src.exists():
        shutil.copy2(src, INSTALL_DIR / MAIN_SCRIPT)
        log_cb(f"     {src} → {INSTALL_DIR / MAIN_SCRIPT}")
    else:
        log_cb(f"[!!] {MAIN_SCRIPT} não encontrado no diretório atual!")
        errors.append("Arquivo principal ausente")
    prog_cb(58, "Script copiado")
    log_cb(_joke())
    time.sleep(0.3)

    # ── Config padrão ─────────────────────────────────────────────
    import json
    cfg_file = CONFIG_DIR / "config.json"
    if not cfg_file.exists():
        log_cb("[>>] Criando config padrão em ~/.novacat/config.json…")
        cfg_file.write_text(json.dumps({
            "abuseipdb_key":  "",
            "virustotal_key": "",
            "theme":          "crimson",
            "comment":        "Adicione chaves API gratuitas. AbuseIPDB: https://www.abuseipdb.com/api"
        }, indent=2))
        log_cb(f"     Criado: {cfg_file}")
    else:
        log_cb("     Config existente mantida.")
    prog_cb(66, "Config criada")
    log_cb(_joke())
    time.sleep(0.3)

    # ── Launcher ──────────────────────────────────────────────────
    log_cb("[>>] Criando launcher ~/.local/bin/novacat…")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    launcher = BIN_DIR / "novacat"
    launcher.write_text(
        f"#!/bin/bash\n"
        f"# NovaCat launcher — gerado pelo installer\n"
        f"# // Um comando. Sem perguntas.\n"
        f"exec {sys.executable} {INSTALL_DIR / MAIN_SCRIPT} \"$@\"\n"
    )
    launcher.chmod(0o755)
    log_cb(f"     Launcher: {launcher}")
    prog_cb(75, "Launcher criado")
    log_cb(_joke())
    time.sleep(0.3)

    # ── .desktop entry ────────────────────────────────────────────
    log_cb("[>>] Criando entrada .desktop para o menu do sistema…")
    DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
    DESKTOP_FILE.write_text(
        f"[Desktop Entry]\n"
        f"Name=NovaCat {VERSION}\n"
        f"Comment=Defensive Threat Intelligence — {CODENAME}\n"
        f"Exec={sys.executable} {INSTALL_DIR / MAIN_SCRIPT}\n"
        f"Icon=security-high\n"
        f"Terminal=false\n"
        f"Type=Application\n"
        f"Categories=System;Security;Network;Utility;\n"
        f"Keywords=security;threat;intelligence;ip;mac;hash;domain;cti;defensive;\n"
        f"StartupNotify=true\n"
    )
    log_cb(f"     .desktop: {DESKTOP_FILE}")
    prog_cb(84, ".desktop criado")
    log_cb(_joke())
    time.sleep(0.3)

    # ── Verifica ferramentas recomendadas ─────────────────────────
    log_cb("[>>] Verificando ferramentas recomendadas no sistema…")
    tools = {
        "ss":       ("iproute2",     "iproute2"),
        "nmap":     ("nmap",         "nmap"),
        "whois":    ("whois",        "whois"),
        "dig":      ("dnsutils",     "bind"),
        "curl":     ("curl",         "curl"),
        "ufw":      ("ufw",          "ufw"),
        "sysctl":   ("procps",       "procps-ng"),
    }
    missing_apt  = []
    missing_pacman = []
    for tool, (pkg_apt, pkg_pacman) in tools.items():
        ok, _ = run_cmd(f"which {tool}")
        if not ok:
            missing_apt.append(pkg_apt)
            missing_pacman.append(pkg_pacman)
    if missing_apt:
        log_cb(f"     [!] Ferramentas opcionais ausentes:")
        log_cb(f"     Arch:   sudo pacman -S {' '.join(set(missing_pacman))}")
        log_cb(f"     Debian: sudo apt install {' '.join(set(missing_apt))}")
    else:
        log_cb("     Todas as ferramentas recomendadas detectadas.")
    prog_cb(95, "Verificação concluída")
    log_cb(_joke())
    time.sleep(0.3)

    # ── PATH check ────────────────────────────────────────────────
    path_env = os.environ.get("PATH", "")
    if str(BIN_DIR) not in path_env:
        log_cb(f"     [!] {BIN_DIR} não está no PATH.")
        log_cb(f"     Adicione ao ~/.bashrc ou ~/.zshrc:")
        log_cb(f"     export PATH=\"$HOME/.local/bin:$PATH\"")

    prog_cb(100, "Instalação concluída!")
    time.sleep(0.3)
    done_cb(errors)


def _is_arch() -> bool:
    """Detecta Arch Linux / Hyprland / derivados."""
    try:
        return Path("/etc/arch-release").exists() or \
               "arch" in Path("/etc/os-release").read_text().lower()
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
#  JANELA DO INSTALLER
# ══════════════════════════════════════════════════════════════════════

class NovaCatInstaller(tk.Tk):
    """
    Janela do installer NovaCat.
    // Frameless, vermelho, com gato. Como toda boa ferramenta de segurança.
    """

    W, H = 860, 640

    def __init__(self):
        super().__init__()
        self.configure(bg=BG)
        self.overrideredirect(True)
        try:
            self.attributes("-alpha", 0.97)
        except Exception:
            pass
        self._center()
        self.geometry(f"{self.W}x{self.H}")
        self._dx = self._dy = 0
        self._penta_items  = []
        self._eye_items    = []
        self._border_item  = None
        self._status_side  = None
        self._build()
        self._animate_glow()
        self._animate_penta()
        self._animate_eyes()

    def _center(self):
        x = (self.winfo_screenwidth()  - self.W) // 2
        y = (self.winfo_screenheight() - self.H) // 2
        self.geometry(f"{self.W}x{self.H}+{x}+{y}")

    def _build(self):
        self.cv = tk.Canvas(self, width=self.W, height=self.H,
                             bg=BG, highlightthickness=0)
        self.cv.pack(fill="both", expand=True)

        self._border_item = self.cv.create_rectangle(
            1, 1, self.W - 1, self.H - 1, outline=GLOW1, width=2)
        self.cv.create_rectangle(
            3, 3, self.W - 3, self.H - 3, outline=BORDER + "55", width=1)

        self.cv.bind("<ButtonPress-1>", self._press)
        self.cv.bind("<B1-Motion>",     self._drag)

        self._draw_cat_panel()
        self._draw_header()
        self._draw_content()

    def _draw_cat_panel(self):
        """Painel lateral com gato + pentagrama. // Ele está te observando."""
        c  = self.cv
        PW = 250
        px = self.W - PW
        cx = px + PW // 2
        cy = 195

        c.create_rectangle(px, 2, self.W - 2, self.H - 2,
                            fill="#060202", outline=BORDER, width=1)
        c.create_line(px, 2, px, self.H - 2, fill=GLOW1, width=1)

        # Corpo
        c.create_oval(cx - 50, cy, cx + 50, cy + 72,
                      fill="#0d0404", outline=GLOW1, width=1)
        # Cauda
        c.create_arc(cx + 28, cy + 25, cx + 85, cy + 95,
                     start=0, extent=210, outline=GLOW1, width=2, style="arc")
        # Cabeça
        c.create_oval(cx - 58, cy - 128, cx + 58, cy - 10,
                      fill="#110606", outline=GLOW1, width=1)
        # Orelhas
        c.create_polygon(cx - 58, cy - 78, cx - 82, cy - 158, cx - 22, cy - 100,
                         fill="#1a0808", outline=GLOW1, width=1)
        c.create_polygon(cx + 58, cy - 78, cx + 82, cy - 158, cx + 22, cy - 100,
                         fill="#1a0808", outline=GLOW1, width=1)
        c.create_polygon(cx - 55, cy - 80, cx - 72, cy - 145, cx - 25, cy - 102,
                         fill=BORDER + "55")
        c.create_polygon(cx + 55, cy - 80, cx + 72, cy - 145, cx + 25, cy - 102,
                         fill=BORDER + "55")

        # Olhos
        for ex in [cx - 20, cx + 20]:
            it = c.create_oval(ex - 13, cy - 75, ex + 13, cy - 48,
                                fill="#1a0000", outline=GLOW1, width=1)
            self._eye_items.append(("bg", it))
            it = c.create_oval(ex - 9,  cy - 72, ex + 9,  cy - 51,
                                fill=GLOW1, outline="")
            self._eye_items.append(("iris", it))
            it = c.create_oval(ex - 4,  cy - 70, ex + 4,  cy - 53,
                                fill="#000000", outline="")
            self._eye_items.append(("pupil", it))
            it = c.create_oval(ex - 7, cy - 71, ex - 3, cy - 66,
                                fill=GLOW3, outline="")
            self._eye_items.append(("glow", it))

        # Nariz e boca
        c.create_polygon(cx - 4, cy - 30, cx + 4, cy - 30, cx, cy - 23,
                         fill=BORDER)
        c.create_line(cx, cy - 23, cx - 7, cy - 16, fill=BORDER, width=1)
        c.create_line(cx, cy - 23, cx + 7, cy - 16, fill=BORDER, width=1)
        for dy in [-5, -2, 1]:
            c.create_line(cx - 50, cy - 32 + dy, cx - 10, cy - 32 + dy,
                          fill=BORDER, width=1)
            c.create_line(cx + 10, cy - 32 + dy, cx + 50, cy - 32 + dy,
                          fill=BORDER, width=1)

        # Pentagrama principal
        pcy = cy + 175
        pr  = 45
        c.create_oval(cx - pr - 7, pcy - pr - 7, cx + pr + 7, pcy + pr + 7,
                      outline=GLOW1, width=2)
        pts = [(cx + pr * math.cos(math.radians(-90 + i * 144)),
                pcy + pr * math.sin(math.radians(-90 + i * 144))) for i in range(5)]
        order = [0, 2, 4, 1, 3, 0]
        for i in range(len(order) - 1):
            x1, y1 = pts[order[i]]
            x2, y2 = pts[order[i + 1]]
            it = c.create_line(x1, y1, x2, y2, fill=GLOW1, width=2)
            self._penta_items.append(it)
        for px2, py2 in pts:
            it = c.create_oval(px2 - 3, py2 - 3, px2 + 3, py2 + 3,
                                fill=GLOW2, outline="")
            self._penta_items.append(it)
        it = c.create_text(cx, pcy, text="✦",
                            font=("Courier New", 12, "bold"), fill=GLOW2)
        self._penta_items.append(it)

        # Sub-pentagramas decorativos
        for (spx, spy, spr) in [(cx - 50, pcy + 58, 10),
                                  (cx,      pcy + 66, 9),
                                  (cx + 50, pcy + 58, 10)]:
            spts = [(spx + spr * math.cos(math.radians(-90 + j * 144)),
                     spy  + spr * math.sin(math.radians(-90 + j * 144))) for j in range(5)]
            sord = [0, 2, 4, 1, 3, 0]
            for k in range(len(sord) - 1):
                x1, y1 = spts[sord[k]]
                x2, y2 = spts[sord[k + 1]]
                c.create_line(x1, y1, x2, y2, fill=BORDER, width=1)

        # Status lateral
        self._status_side = c.create_text(cx, pcy + 88, text="AGUARDANDO",
                                           font=("Courier New", 9, "bold"), fill=MUTED)
        c.create_text(cx, pcy + 104, text=f"v{VERSION}",
                      font=("Courier New", 7), fill=DIM)

    def _draw_header(self):
        c  = self.cv
        PW = 250
        c.create_rectangle(0, 0, self.W - PW, 52, fill=BG2, outline="")
        c.create_line(0, 52, self.W - PW, 52, fill=GLOW1, width=1)

        c.create_text(18, 26, text="◈", font=("Courier New", 16, "bold"),
                      fill=GLOW2, anchor="w")
        c.create_text(46, 15, text=f"{NAME} — Installer",
                      font=("Courier New", 13, "bold"), fill=TEXT, anchor="w")
        c.create_text(46, 35, text=f"v{VERSION}  ·  {CODENAME}  ·  Defensive Threat Intelligence",
                      font=("Courier New", 8), fill=MUTED, anchor="w")

        close = c.create_text(self.W - PW - 22, 26, text="✕",
                               font=("Courier New", 13, "bold"), fill=MUTED)
        c.tag_bind(close, "<Enter>",    lambda e: c.itemconfigure(close, fill=GLOW1))
        c.tag_bind(close, "<Leave>",    lambda e: c.itemconfigure(close, fill=MUTED))
        c.tag_bind(close, "<Button-1>", lambda e: self.destroy())

    def _draw_content(self):
        c  = self.cv
        PW = 250
        MW = self.W - PW

        # Destino
        c.create_line(0, 82, MW, 82, fill=BORDER + "44", width=1)
        c.create_text(20, 70, text="Destino:",
                      font=("Courier New", 9), fill=MUTED, anchor="w")
        c.create_text(88, 70, text=str(INSTALL_DIR),
                      font=("Courier New", 9, "bold"), fill=TEXT, anchor="w")

        # Componentes
        c.create_text(20, 100, text="NovaCat — Componentes:",
                      font=("Courier New", 10, "bold"), fill=GLOW2, anchor="w")

        items = [
            ("◈", "Lookup de IP  ·  Geolocalização  ·  AbuseIPDB  ·  OTX"),
            ("⚡", "Análise de MAC  ·  OUI  ·  Fabricante  ·  Spoofing detect"),
            ("🧬", "Verificação de Hash  ·  MalwareBazaar  ·  ThreatFox"),
            ("🌐", "Reputação de Domínio  ·  URLhaus  ·  DNS resolve"),
            ("📋", "Log de consultas  ·  Config ~/.novacat/config.json"),
            ("🔑", "API Keys opcionais  ·  AbuseIPDB  ·  VirusTotal (free)"),
        ]
        for i, (icon, desc) in enumerate(items):
            y = 122 + i * 26
            c.create_text(22, y, text=icon,
                          font=("Courier New", 10), fill=GLOW1, anchor="w")
            c.create_text(46, y, text=desc,
                          font=("Courier New", 9),  fill=MUTED,  anchor="w")

        # Barra de progresso
        c.create_line(0, 308, MW, 308, fill=BORDER + "55", width=1)
        c.create_text(20, 322, text="Progresso:",
                      font=("Courier New", 9), fill=MUTED, anchor="w")

        c.create_rectangle(20, 334, MW - 22, 352,
                            fill="#100404", outline=BORDER, width=1)
        self._prog_bar = c.create_rectangle(20, 334, 20, 352,
                                             fill=GLOW1, outline="")
        self._prog_pct = c.create_text((MW // 2), 343, text="0%",
                                        font=("Courier New", 9, "bold"), fill=TEXT)
        self._status_text = c.create_text(20, 360, text="Aguardando…",
                                           font=("Courier New", 9), fill=MUTED, anchor="w")

        # Log box
        self._log_frame = tk.Frame(self, bg=BG3)
        self._log_frame.place(x=18, y=375, width=MW - 36, height=160)
        self._log_txt = tk.Text(self._log_frame,
                                 bg="#060101", fg=MONO,
                                 font=("Courier New", 8), relief="flat", bd=0,
                                 state="disabled", wrap="word")
        sb = tk.Scrollbar(self._log_frame, orient="vertical",
                           command=self._log_txt.yview,
                           bg=BG, troughcolor=BG, activebackground=GLOW1,
                           relief="flat", bd=0)
        self._log_txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_txt.pack(fill="both", expand=True)
        c.create_rectangle(17, 374, MW - 17, 536, outline=BORDER, width=1)

        # Botões
        self._btn_install = tk.Button(self,
            text="▶  INSTALAR NOVACAT",
            font=("Courier New", 12, "bold"),
            bg=GLOW1, fg="#fff",
            activebackground=BORDER, activeforeground="#fff",
            relief="flat", bd=0, cursor="hand2",
            command=self._start_install)
        self._btn_install.place(x=18, y=546, width=280, height=42)

        self._btn_launch = tk.Button(self,
            text="🚀  INICIAR NOVACAT",
            font=("Courier New", 11, "bold"),
            bg="#120505", fg=MUTED,
            activebackground=BG3, activeforeground=TEXT,
            relief="flat", bd=0, cursor="arrow",
            state="disabled",
            command=self._launch)
        self._btn_launch.place(x=310, y=546, width=MW - 328, height=42)

    # ── Animações ────────────────────────────────────────────────────

    def _animate_glow(self):
        colors = [GLOW1,"#d42020","#dc2626","#e03030",
                  "#dc2626",GLOW1,"#b01010","#980d0d","#b01010",GLOW1]
        idx = [0]
        def tick():
            if not self.winfo_exists(): return
            self.cv.itemconfigure(self._border_item,
                                   outline=colors[idx[0] % len(colors)])
            idx[0] += 1
            self.after(110, tick)
        tick()

    def _animate_penta(self):
        reds = ["#8b0000","#a01010",GLOW1,"#dc2626",GLOW2,
                "#dc2626",GLOW1,"#a01010","#8b0000"]
        idx = [0]
        def tick():
            if not self.winfo_exists(): return
            col = reds[idx[0] % len(reds)]
            for it in self._penta_items:
                try: self.cv.itemconfigure(it, fill=col, outline=col)
                except: pass
            idx[0] += 1
            self.after(140, tick)
        tick()

    def _animate_eyes(self):
        """Olhos do instalador também pulsam. // Ele sabe que você vai instalar."""
        reds = [GLOW1,"#d42020",GLOW2,"#ff4444",GLOW2,GLOW1,"#b01010"]
        gls  = [GLOW3,"#ff9999","#ffbbbb",GLOW3,GLOW2]
        idx  = [0]
        def tick():
            if not self.winfo_exists(): return
            col = reds[idx[0] % len(reds)]
            gcol= gls[idx[0] % len(gls)]
            for kind, it in self._eye_items:
                try:
                    if kind == "iris": self.cv.itemconfigure(it, fill=col)
                    if kind == "glow": self.cv.itemconfigure(it, fill=gcol)
                except: pass
            idx[0] += 1
            self.after(160, tick)
        tick()

    # ── Arraste ──────────────────────────────────────────────────────

    def _press(self, e):
        self._dx = e.x
        self._dy = e.y

    def _drag(self, e):
        self.geometry(f"+{self.winfo_x() + e.x - self._dx}"
                      f"+{self.winfo_y() + e.y - self._dy}")

    # ── Log / Progresso ──────────────────────────────────────────────

    def _log(self, msg):
        def _do():
            self._log_txt.configure(state="normal")
            self._log_txt.insert("end", msg + "\n")
            self._log_txt.see("end")
            self._log_txt.configure(state="disabled")
        try: self._log_txt.after(0, _do)
        except: pass

    def _prog(self, pct, msg=""):
        PW = 250
        MW = self.W - PW
        bar_w = int(pct / 100 * (MW - 40))
        def _do():
            self.cv.coords(self._prog_bar, 20, 334, 20 + bar_w, 352)
            self.cv.itemconfigure(self._prog_pct, text=f"{pct}%")
            if msg:
                self.cv.itemconfigure(self._status_text, text=msg[:70])
        try: self.cv.after(0, _do)
        except: pass

    def _done(self, errors):
        def _do():
            if errors:
                msg = f"⚠ Concluído com {len(errors)} aviso(s)"
                col = WARNING
            else:
                msg = "✓ Instalação concluída com sucesso!"
                col = SUCCESS
            try:
                self.cv.itemconfigure(self._status_text, text=msg, fill=col)
                if self._status_side:
                    self.cv.itemconfigure(self._status_side,
                                           text="INSTALADO" + (" ⚠" if errors else " ✓"),
                                           fill=col)
            except: pass
            self._btn_install.configure(state="disabled", bg="#1a0808")
            self._btn_launch.configure(state="normal", bg=GLOW1, fg="#fff",
                                        activebackground=BORDER, cursor="hand2")
        try: self.cv.after(0, _do)
        except: pass

    def _start_install(self):
        self._btn_install.configure(state="disabled", text="Instalando…")
        self._log(f"◈ {NAME} — Iniciando instalação…")
        self._log(f"   Sistema: {_is_arch() and 'Arch Linux detectado' or 'Linux'}")
        self._log("─" * 52)
        threading.Thread(
            target=do_install,
            args=(self._log, self._prog, self._done),
            daemon=True
        ).start()

    def _launch(self):
        target = INSTALL_DIR / MAIN_SCRIPT
        if target.exists():
            import subprocess as sp
            sp.Popen([sys.executable, str(target)])
            self.after(800, self.destroy)
        else:
            self._log(f"[!] Não encontrado: {target}")
            self._log("    Execute o installer novamente.")


if __name__ == "__main__":
    app = NovaCatInstaller()
    app.mainloop()
