#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║   NovaCat — Build Script  (PyInstaller)                             ║
║   Gera executável único: gato vermelho + pentagrama                 ║
║                                                                      ║
║   Uso:                                                               ║
║     python build_novacat.py                                          ║
║     python build_novacat.py --clean-only                             ║
║     python build_novacat.py --icon-only                              ║
║                                                                      ║
║   Pré-requisitos:                                                    ║
║     pip install pyinstaller Pillow psutil                            ║
║     Arch: sudo pacman -S python-pyinstaller python-pillow python-psutil ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import subprocess, sys, os, shutil, math, platform
from pathlib import Path

# ── Config do build ──────────────────────────────────────────────────
APP_NAME      = "NovaCat"
INSTALLER_SCRIPT = "novacat_installer.py"   # entry point = installer
MAIN_SCRIPT      = "NovaCat.py"             # bundled junto
VERSION          = "1.0.0"
CODENAME         = "VELVET DAGGER"
ICON_PNG         = "novacat_icon.png"

# // Build script: onde o código vira binário e a documentação vira opcional.


def check_pyinstaller() -> bool:
    """Verifica ou instala PyInstaller."""
    try:
        import PyInstaller
        print(f"[+] PyInstaller {PyInstaller.__version__} disponível.")
        return True
    except ImportError:
        print("[*] Instalando PyInstaller…")
        flags = "--break-system-packages" if _is_arch() else ""
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"] + (flags.split() if flags else []),
            capture_output=True, text=True
        )
        if r.returncode == 0:
            print("[+] PyInstaller instalado.")
            return True
        print(f"[-] Falha ao instalar PyInstaller: {r.stderr[:200]}")
        return False


def _is_arch() -> bool:
    """Arch Linux detectado. // A distro que compila tudo, inclusive paciência."""
    try:
        return Path("/etc/arch-release").exists()
    except Exception:
        return False


def generate_icon() -> str | None:
    """
    Gera ícone PNG 256×256: gato de olhos vermelhos + pentagrama.
    // Um ícone que diz 'eu vejo você' antes mesmo de abrir.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("[*] Instalando Pillow para geração de ícone…")
        flags = ["--break-system-packages"] if _is_arch() else []
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"] + flags,
                       capture_output=True)
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            print("[!] Pillow indisponível — build prossegue sem ícone.")
            return None

    print("[*] Gerando ícone NovaCat (256×256)…")
    SIZE = 256
    img  = Image.new("RGBA", (SIZE, SIZE), (5, 3, 3, 255))
    d    = ImageDraw.Draw(img)

    # Paleta
    RED1   = (204, 26,  26)
    RED2   = (255, 51,  51)
    RED3   = (255, 96,  96)
    DARK   = (17,  6,   6)
    DBORD  = (139, 0,   0)
    DARKER = (11,  3,   3)

    cx, cy = SIZE // 2, SIZE // 2 - 10

    # Círculo externo do ícone
    d.ellipse([4, 4, SIZE - 4, SIZE - 4], outline=RED1, width=2)
    d.ellipse([8, 8, SIZE - 8, SIZE - 8], outline=(80, 0, 0), width=1)

    # Corpo do gato
    d.ellipse([cx - 50, cy + 5, cx + 50, cy + 68],
              fill=DARKER, outline=RED1, width=1)

    # Cauda
    d.arc([cx + 28, cy + 25, cx + 82, cy + 85],
          start=0, end=210, fill=RED1, width=2)

    # Cabeça
    d.ellipse([cx - 58, cy - 122, cx + 58, cy - 5],
              fill=DARK, outline=RED1, width=2)

    # Orelhas
    d.polygon([cx - 58, cy - 72, cx - 84, cy - 152, cx - 22, cy - 94],
              fill=(26, 8, 8), outline=RED1)
    d.polygon([cx + 58, cy - 72, cx + 84, cy - 152, cx + 22, cy - 94],
              fill=(26, 8, 8), outline=RED1)
    d.polygon([cx - 55, cy - 74, cx - 72, cy - 140, cx - 25, cy - 96],
              fill=(80, 0, 0, 100))
    d.polygon([cx + 55, cy - 74, cx + 72, cy - 140, cx + 25, cy - 96],
              fill=(80, 0, 0, 100))

    # Olhos vermelhos — o destaque da peça
    for ex in [cx - 20, cx + 20]:
        d.ellipse([ex - 13, cy - 72, ex + 13, cy - 46],
                  fill=(26, 0, 0), outline=RED2, width=2)
        d.ellipse([ex - 9,  cy - 69, ex + 9,  cy - 49], fill=RED1)
        d.ellipse([ex - 4,  cy - 67, ex + 4,  cy - 51], fill=(0, 0, 0))
        # Brilho do olho
        d.ellipse([ex - 8, cy - 68, ex - 3, cy - 62], fill=RED3)

    # Nariz e boca
    d.polygon([cx - 5, cy - 28, cx + 5, cy - 28, cx, cy - 20], fill=DBORD)
    d.line([cx, cy - 20, cx - 7, cy - 13, cx - 14, cy - 10],
           fill=DBORD, width=1)
    d.line([cx, cy - 20, cx + 7, cy - 13, cx + 14, cy - 10],
           fill=DBORD, width=1)

    # Bigodes
    for dy in [-5, -2, 1]:
        d.line([cx - 50, cy - 30 + dy, cx - 10, cy - 30 + dy], fill=DBORD, width=1)
        d.line([cx + 10, cy - 30 + dy, cx + 50, cy - 30 + dy], fill=DBORD, width=1)

    # Pentagrama abaixo do gato
    pr  = 36
    pcx = cx
    pcy = cy + 118
    d.ellipse([pcx - pr - 5, pcy - pr - 5, pcx + pr + 5, pcy + pr + 5],
              outline=RED1, width=2)
    d.ellipse([pcx - pr - 9, pcy - pr - 9, pcx + pr + 9, pcy + pr + 9],
              outline=(80, 0, 0), width=1)

    pts = [(pcx + pr * math.cos(math.radians(-90 + i * 144)),
            pcy + pr * math.sin(math.radians(-90 + i * 144))) for i in range(5)]
    order = [0, 2, 4, 1, 3, 0]
    for i in range(len(order) - 1):
        x1, y1 = pts[order[i]]
        x2, y2 = pts[order[i + 1]]
        d.line([x1, y1, x2, y2], fill=RED1, width=2)
    for px2, py2 in pts:
        d.ellipse([px2 - 3, py2 - 3, px2 + 3, py2 + 3], fill=RED2)

    img.save(ICON_PNG, format="PNG")
    print(f"[+] Ícone salvo: {ICON_PNG}")

    # ICO para Windows (se aplicável)
    if platform.system() == "Windows":
        ico_path = "novacat.ico"
        img.save(ico_path, format="ICO",
                 sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"[+] Ícone ICO: {ico_path}")
        return ico_path

    return ICON_PNG


def check_scripts() -> bool:
    """Verifica se os scripts necessários existem."""
    ok = True
    for f in [INSTALLER_SCRIPT, MAIN_SCRIPT]:
        if Path(f).exists():
            print(f"[+] Encontrado: {f}")
        else:
            print(f"[-] FALTANDO: {f}")
            ok = False
    return ok


def build():
    """
    Executa o build via PyInstaller.
    // Um executável standalone. O alvo vai agradecer a portabilidade.
    """
    print()
    print("=" * 68)
    print(f"  {APP_NAME}  v{VERSION}  —  {CODENAME}")
    print("  Build Script · PyInstaller · Linux / Arch / Hyprland")
    print("=" * 68)
    print()

    plat = platform.system()
    arch = platform.machine()
    print(f"[i] Plataforma: {plat} {arch}")
    print(f"[i] Python:     {sys.version.split()[0]}")
    if _is_arch():
        print("[i] Arch Linux detectado — usando --break-system-packages onde necessário")
    print()

    if not check_pyinstaller():
        sys.exit(1)

    if not check_scripts():
        print(f"\n[-] Coloque {INSTALLER_SCRIPT} e {MAIN_SCRIPT}")
        print("    no mesmo diretório que este script e tente novamente.")
        sys.exit(1)

    icon_path = generate_icon()

    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",       # binário único — portátil e discreto
        "--windowed",      # sem terminal — como deve ser
        "--name",  APP_NAME,
        "--clean",
        "--noconfirm",
    ]

    if icon_path and Path(icon_path).exists():
        cmd += ["--icon", icon_path]

    # Bundla NovaCat.py junto ao installer
    sep = os.pathsep
    cmd += ["--add-data", f"{MAIN_SCRIPT}{sep}."]

    # Hidden imports — tudo que tkinter e psutil precisam
    hidden = [
        "tkinter", "tkinter.font", "tkinter.messagebox",
        "tkinter.ttk", "tkinter.scrolledtext",
        "psutil", "psutil._pslinux", "psutil._psposix",
        "pathlib", "hashlib", "threading", "subprocess",
        "shutil", "json", "re", "math", "random",
        "datetime", "socket", "platform",
        "urllib", "urllib.request", "urllib.parse", "urllib.error",
        "ctypes", "struct",
    ]
    for hi in hidden:
        cmd += ["--hidden-import", hi]

    cmd += [
        "--collect-submodules", "psutil",
        "--collect-data",       "psutil",
    ]

    cmd.append(INSTALLER_SCRIPT)

    print(f"\n[>] Iniciando PyInstaller…")
    print(f"    Entry:  {INSTALLER_SCRIPT}")
    print(f"    Bundle: {MAIN_SCRIPT}")
    print(f"    Output: dist/{APP_NAME}")
    if _is_arch():
        print("    Nota:   Em Hyprland/Wayland use  GDK_BACKEND=x11 ./NovaCat")
    print()

    result = subprocess.run(cmd, text=True)

    if result.returncode == 0:
        print()
        print("=" * 68)
        print("  BUILD CONCLUÍDO COM SUCESSO!")
        print("=" * 68)
        ext = ".exe" if platform.system() == "Windows" else ""
        exe = Path("dist") / f"{APP_NAME}{ext}"
        if exe.exists():
            size = exe.stat().st_size / 1024 / 1024
            print(f"\n  Executável : {exe}")
            print(f"  Tamanho    : {size:.1f} MB")
            print(f"  Plataforma : {platform.system()} {platform.machine()}")
        print()
        print("  Para executar:")
        print(f"    ./dist/{APP_NAME}                           (Linux/Arch)")
        print(f"    GDK_BACKEND=x11 ./dist/{APP_NAME}          (Wayland/Hyprland)")
        print()
        print("  Para instalar manualmente:")
        print(f"    ./dist/{APP_NAME}   (abre o installer GUI)")
        print()
        # // Build concluído. O executável está pronto. O alvo, talvez não.
    else:
        print("\n[-] BUILD FALHOU.")
        print("    Verifique os erros acima.")
        print()
        print("  Dicas de diagnóstico:")
        print("    pip install psutil Pillow pyinstaller")
        if _is_arch():
            print("    sudo pacman -S tk python-psutil python-pillow")
            print("    GDK_BACKEND=x11  (se rodar em Wayland/Hyprland)")
        else:
            print("    sudo apt install python3-tk python3-dev")
        sys.exit(1)


def clean():
    """Remove artefatos do build anterior."""
    for item in [f"{APP_NAME}.spec", "build", ICON_PNG]:
        p = Path(item)
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            print(f"[*] Removido: {item}")
    print("[*] Limpeza concluída.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description=f"Build Script — {APP_NAME} v{VERSION} — {CODENAME}"
    )
    ap.add_argument("--clean-only", action="store_true",
                    help="Apenas remove artefatos de builds anteriores")
    ap.add_argument("--icon-only",  action="store_true",
                    help="Apenas gera o ícone PNG/ICO")
    args = ap.parse_args()

    if args.clean_only:
        clean()
    elif args.icon_only:
        generate_icon()
    else:
        build()
        clean()
