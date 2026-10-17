"""Gera traducao_ptbr.bin (so o texto em portugues + hashes) a partir dos JSONs de trabalho.
Uso: python build_patch.py
"""
import hashlib
import json
import zlib
from pathlib import Path

import patchcore as pc

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools'
EN = ROOT / 'Data' / 'DATA' / 'EN'
VERSAO = '1.2'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    db_orig = (EN / 'DATABASE_EN.dat.bak').read_bytes()
    gs_orig = (EN / 'EN_GameString.dat.bak').read_bytes()

    talk = json.loads((TOOLS / 'talk_ptbr.json').read_text(encoding='utf-8-sig'))['strings']
    talk_map = {s['index']: s['translated'].strip() for s in talk if s.get('translated', '').strip()}

    gs = json.loads((TOOLS / 'gamestring_ptbr.json').read_text(encoding='utf-8-sig'))
    gs_map = {s['id']: s['translated'].strip() for s in gs if s.get('translated', '').strip()}

    desc = json.loads((TOOLS / 'desc_ptbr.json').read_text(encoding='utf-8'))['strings']
    by_text = {s['original']: s['translated'] for s in desc if s.get('translated')}
    field_map = {}
    for name, r, k, _, _, text in pc.iter_text_fields(db_orig):
        if text in by_text:
            field_map[(name, r, k)] = by_text[text]
    pos = json.loads((TOOLS / 'pos_ptbr.json').read_text(encoding='utf-8'))
    for name, recs in pos.items():
        for r, lines in recs.items():
            for k, line in enumerate(lines):
                field_map[(name, int(r), k)] = line

    db_new = pc.apply_fields(pc.apply_talk(db_orig, talk_map), field_map)
    gs_new = pc.apply_gamestring(gs_orig, gs_map)

    cur_db = (EN / 'DATABASE_EN.dat').read_bytes()
    cur_gs = (EN / 'EN_GameString.dat').read_bytes()
    print('DATABASE igual ao do jogo:', db_new == cur_db)
    print('GameString igual ao do jogo:', gs_new == cur_gs)

    payload = {
        'versao': VERSAO,
        'autor': 'Maykin',
        'hashes': {
            'DATABASE_EN.dat': {'original': sha(db_orig), 'traduzido': sha(db_new), 'tamanho_original': len(db_orig)},
            'EN_GameString.dat': {'original': sha(gs_orig), 'traduzido': sha(gs_new), 'tamanho_original': len(gs_orig)},
        },
        'talk': {str(k): v for k, v in talk_map.items()},
        'gamestring': {str(k): v for k, v in gs_map.items()},
        'fields': [[n, r, k, t] for (n, r, k), t in field_map.items()],
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    out = Path(__file__).with_name('traducao_ptbr.bin')
    out.write_bytes(b'D4PTBR1\n' + zlib.compress(raw, 9))
    print(f'{out.name}: {out.stat().st_size / 1024:.0f} KB | talk {len(talk_map)} | ui {len(gs_map)} | campos {len(field_map)}')


if __name__ == '__main__':
    main()
