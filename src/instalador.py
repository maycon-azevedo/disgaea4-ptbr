"""Instalador da Traducao PT-BR de Disgaea 4 Complete+ (por Maykin)."""
import hashlib
import json
import os
import shutil
import sys
import threading
import zlib
from pathlib import Path

import patchcore as pc

TITULO = 'Disgaea 4 Complete+ — Tradução PT-BR'
CREDITOS = 'Tradução por Maykin'
PASTA_JOGO = 'Disgaea 4 Complete+'
REL_EN = Path('Data') / 'DATA' / 'EN'
ARQS = ['DATABASE_EN.dat', 'EN_GameString.dat']
BACKUP = 'backup_original_ptbr'


def recurso(nome):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    return base / nome


def carregar_patch():
    raw = recurso('traducao_ptbr.bin').read_bytes()
    assert raw.startswith(b'D4PTBR1\n'), 'arquivo de dados inválido'
    return json.loads(zlib.decompress(raw[8:]).decode('utf-8'))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for bloco in iter(lambda: f.read(1 << 20), b''):
            h.update(bloco)
    return h.hexdigest()


def pastas_steam():
    cands = []
    try:
        import winreg
        for raiz, chave in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'),
                            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')]:
            try:
                with winreg.OpenKey(raiz, chave) as k:
                    for nome in ('SteamPath', 'InstallPath'):
                        try:
                            cands.append(Path(winreg.QueryValueEx(k, nome)[0]))
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    cands += [Path(r'C:\Program Files (x86)\Steam'), Path(r'C:\Program Files\Steam')]
    libs = []
    for s in cands:
        vdf = s / 'steamapps' / 'libraryfolders.vdf'
        libs.append(s)
        if vdf.exists():
            for linha in vdf.read_text(encoding='utf-8', errors='ignore').splitlines():
                linha = linha.strip()
                if linha.startswith('"path"'):
                    libs.append(Path(linha.split('"')[3].replace('\\\\', '\\')))
    return libs


def achar_jogo():
    candidatos = []
    exe = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).resolve()
    candidatos += [exe.parent, *exe.parents]
    for lib in pastas_steam():
        candidatos.append(lib / 'steamapps' / 'common' / PASTA_JOGO)
    for letra in 'CDEFGHIJ':
        for sub in ('SteamLibrary', 'Steam', r'Program Files (x86)\Steam', 'Jogos\\Steam', 'Games\\Steam'):
            candidatos.append(Path(f'{letra}:\\') / sub / 'steamapps' / 'common' / PASTA_JOGO)
    for c in candidatos:
        if (c / REL_EN / 'DATABASE_EN.dat').exists():
            return c
    return None


def normalizar_pasta(p):
    p = Path(p)
    for c in [p, *p.parents]:
        if (c / REL_EN / 'DATABASE_EN.dat').exists():
            return c
    return None


def estado(jogo, patch):
    """Retorna 'original', 'traduzido' ou 'desconhecido'."""
    en = jogo / REL_EN
    st = set()
    for a in ARQS:
        h = sha(en / a)
        info = patch['hashes'][a]
        st.add('original' if h == info['original'] else 'traduzido' if h == info['traduzido'] else 'desconhecido')
    return st.pop() if len(st) == 1 else 'desconhecido'


def backup_valido(jogo, patch):
    b = jogo / REL_EN / BACKUP
    return all((b / a).exists() and sha(b / a) == patch['hashes'][a]['original'] for a in ARQS)


def instalar(jogo, patch, log):
    en = jogo / REL_EN
    est = estado(jogo, patch)
    if est == 'traduzido':
        log('A tradução já está instalada nesta versão.')
        return True
    if est == 'original':
        fonte = en
    elif backup_valido(jogo, patch):
        log('Arquivos atuais não são os originais; usando o backup original salvo.')
        fonte = en / BACKUP
    else:
        log('ERRO: os arquivos do jogo não batem com a versão suportada.\n'
            'Possíveis causas: o jogo foi atualizado ou há outro mod instalado.\n'
            'Tente "Verificar integridade dos arquivos" na Steam e rode o instalador de novo.')
        return False
    bk = en / BACKUP
    bk.mkdir(exist_ok=True)
    for a in ARQS:
        if not ((bk / a).exists() and sha(bk / a) == patch['hashes'][a]['original']):
            shutil.copy2(fonte / a, bk / a)
    log('Backup dos arquivos originais criado.')

    log('Aplicando diálogos (isso pode levar alguns segundos)...')
    db = (bk / 'DATABASE_EN.dat').read_bytes()
    db = pc.apply_talk(db, {int(k): v for k, v in patch['talk'].items()})
    log('Aplicando descrições, itens, skills e falas de NPC...')
    db = pc.apply_fields(db, {(n, r, k): t for n, r, k, t in patch['fields']})
    log('Aplicando interface...')
    gs = pc.apply_gamestring((bk / 'EN_GameString.dat').read_bytes(), {int(k): v for k, v in patch['gamestring'].items()})

    if hashlib.sha256(db).hexdigest() != patch['hashes']['DATABASE_EN.dat']['traduzido'] or \
       hashlib.sha256(gs).hexdigest() != patch['hashes']['EN_GameString.dat']['traduzido']:
        log('ERRO: o resultado não confere. Nada foi alterado.')
        return False
    for nome, dados in (('DATABASE_EN.dat', db), ('EN_GameString.dat', gs)):
        tmp = en / (nome + '.tmp_ptbr')
        tmp.write_bytes(dados)
        os.replace(tmp, en / nome)
    log('Tradução instalada com sucesso! Pode abrir o jogo.')
    return True


def desinstalar(jogo, patch, log):
    en = jogo / REL_EN
    if estado(jogo, patch) == 'original':
        log('O jogo já está com os arquivos originais (em inglês).')
        return True
    if not backup_valido(jogo, patch):
        log('ERRO: backup original não encontrado.\n'
            'Use "Verificar integridade dos arquivos" na Steam para voltar ao inglês.')
        return False
    for a in ARQS:
        shutil.copy2(en / BACKUP / a, en / a)
    log('Arquivos originais restaurados. O jogo voltou para o inglês.')
    return True


def gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox

    patch = carregar_patch()
    root = tk.Tk()
    root.title(TITULO)
    root.resizable(False, False)
    pad = {'padx': 14, 'pady': 6}

    tk.Label(root, text=TITULO, font=('Segoe UI', 14, 'bold')).pack(**pad)
    tk.Label(root, text=f"{CREDITOS} — versão {patch['versao']}", font=('Segoe UI', 10)).pack()

    fr = tk.Frame(root)
    fr.pack(fill='x', **pad)
    tk.Label(fr, text='Pasta do jogo:').pack(anchor='w')
    pasta = tk.StringVar(value=str(achar_jogo() or ''))
    linha = tk.Frame(fr)
    linha.pack(fill='x')
    tk.Entry(linha, textvariable=pasta, width=62).pack(side='left', fill='x', expand=True)

    def escolher():
        d = filedialog.askdirectory(title='Selecione a pasta "Disgaea 4 Complete+"')
        if d:
            pasta.set(d)
            atualizar()
    tk.Button(linha, text='Procurar...', command=escolher).pack(side='left', padx=6)

    status = tk.Label(root, text='', font=('Segoe UI', 10, 'bold'))
    status.pack(**pad)
    caixa = tk.Text(root, width=72, height=9, state='disabled', font=('Consolas', 9))
    caixa.pack(**pad)

    def log(msg):
        def f():
            caixa.config(state='normal')
            caixa.insert('end', msg + '\n')
            caixa.see('end')
            caixa.config(state='disabled')
        root.after(0, f)

    botoes = tk.Frame(root)
    botoes.pack(**pad)

    def jogo_atual():
        j = normalizar_pasta(pasta.get()) if pasta.get() else None
        if not j:
            messagebox.showerror(TITULO, 'Pasta do jogo não encontrada.\nClique em "Procurar..." e selecione a pasta "Disgaea 4 Complete+".')
        return j

    def atualizar():
        j = normalizar_pasta(pasta.get()) if pasta.get() else None
        if not j:
            status.config(text='Jogo não encontrado — selecione a pasta.', fg='#b00')
            return
        pasta.set(str(j))
        e = estado(j, patch)
        txt = {'original': ('Status: jogo em inglês (original)', '#333'),
               'traduzido': ('Status: tradução PT-BR instalada ✔', '#070'),
               'desconhecido': ('Status: versão desconhecida / modificada', '#b60')}[e]
        status.config(text=txt[0], fg=txt[1])

    def rodar(func):
        j = jogo_atual()
        if not j:
            return
        for b in botoes.winfo_children():
            b.config(state='disabled')

        def trabalho():
            try:
                ok = func(j, patch, log)
            except PermissionError:
                ok = False
                log('ERRO: sem permissão para gravar. Feche o jogo e tente executar como administrador.')
            except Exception as ex:
                ok = False
                log(f'ERRO inesperado: {ex}')

            def fim():
                for b in botoes.winfo_children():
                    b.config(state='normal')
                atualizar()
                (messagebox.showinfo if ok else messagebox.showerror)(TITULO, 'Concluído!' if ok else 'Não foi possível concluir. Veja as mensagens na janela.')
            root.after(0, fim)
        threading.Thread(target=trabalho, daemon=True).start()

    tk.Button(botoes, text='Instalar tradução', width=20, command=lambda: rodar(instalar)).pack(side='left', padx=6)
    tk.Button(botoes, text='Desinstalar (voltar ao inglês)', width=26, command=lambda: rodar(desinstalar)).pack(side='left', padx=6)
    tk.Label(root, text='Feche o jogo antes de instalar. O jogo deve estar em Inglês nas configurações.',
             font=('Segoe UI', 8), fg='#555').pack(pady=(0, 10))
    atualizar()
    if not pasta.get():
        log('Não encontrei o jogo automaticamente. Clique em "Procurar..." e selecione a pasta do jogo.')
    root.mainloop()


def cli():
    patch = carregar_patch()
    acao, pasta = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
    jogo = normalizar_pasta(pasta) if pasta else achar_jogo()
    if not jogo:
        print('Jogo não encontrado.')
        sys.exit(2)
    ok = {'--instalar': instalar, '--desinstalar': desinstalar}[acao](jogo, patch, print) if acao != '--status' else print(estado(jogo, patch)) or True
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].startswith('--'):
        cli()
    else:
        gui()
