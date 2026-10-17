"""Aplicacao da traducao PT-BR em memoria (usado pelo gerador do patch e pelo instalador)."""
import bisect
import re
import struct

TEXT_FIELDS = {
    'mitem.dat': (244, [(96, 128)]),
    'magic.dat': (356, [(56, 128)]),
    'mskill.dat': (212, [(79, 128)]),
    'HABIT.dat': (224, [(72, 128)]),
    'charhelp.dat': (386, [(2, 128), (130, 128), (258, 128)]),
    'zukan.dat': (1092, [(68, 128)] + [(196 + 128 * k, 128) for k in range(7)]),
    'WISH.dat': (304, [(40, 128), (168, 128)]),
    'TownEditMessage.dat': (390, [(6, 128), (134, 128), (262, 128)]),
    'Torture.dat': (436, [(2, 64), (66, 128)]),
    'TortureNegotiation.dat': (208, [(2, 64), (66, 128)]),
    'ShipParts.dat': (616, [(354, 128), (482, 128)]),
    'NetworkHistory.dat': (130, [(2, 128)]),
    'RelatedChart.dat': (468, [(2, 64), (66, 128), (194, 128), (322, 128)]),
    'MinistryMap.dat': (186, [(2, 32), (49, 128)]),
    'CheatShopInformation.dat': (726, [(2, 44)] + [(46 + 68 * k, 68) for k in range(10)]),
    'GE.dat': (196, [(2, 64), (66, 128)]),
    'charPersonal.dat': (70, [(5, 64)]),
    'UserFavoriteFood.dat': (66, [(2, 64)]),
    'UserHobby.dat': (66, [(2, 64)]),
    'UserLocation.dat': (66, [(2, 64)]),
    'THIEF.dat': (70, [(6, 64)]),
    'committee.dat': (616, [(204, 128), (332, 128), (460, 128)]),
    'EventViewer.dat': (136, [(8, 92)]),
}


def parse_nsac(data):
    files = {}
    for m in re.finditer(rb'([a-zA-Z_][a-zA-Z0-9_]{1,30})\.dat', data[:3000]):
        name = m.group(1).decode() + '.dat'
        offset, size = struct.unpack_from('<II', data, m.start() - 8)
        files[name] = (offset, size)
    return files


def apply_talk(db, talk_map):
    """talk_map: {indice_do_texto: texto}. Retorna novo DATABASE (bytes)."""
    db_data = bytearray(db)
    talk_off, talk_size = parse_nsac(bytes(db_data))['talk.dat']
    talk_data = bytearray(db_data[talk_off:talk_off + talk_size])
    count = struct.unpack_from('<I', talk_data, 0)[0]
    header_size, record_size = 16, 56
    script_start = header_size + count * record_size
    records = [list(struct.unpack_from('<14I', talk_data, header_size + i * record_size)) for i in range(count)]
    script = bytearray(talk_data[script_start:])

    positions = []
    i = idx = 0
    while i < len(script) - 2:
        if script[i] == 0x01 and script[i + 1] >= 0x20:
            start = i + 1
            end = start
            while end < len(script) and script[end] != 0x00:
                end += 1
            raw = script[start:end]
            try:
                text = raw.decode('utf-8', errors='strict')
                if len(text) >= 2 and sum(1 for c in text if c.isprintable()) > len(text) * 0.7:
                    positions.append((idx, i, start, end, bytes(raw)))
                    idx += 1
            except UnicodeDecodeError:
                pass
            i = end + 1 if end > start else i + 1
        else:
            i += 1

    new_script = bytearray()
    last_end = shift = 0
    shifts = []
    for tidx, marker, start, end, raw in positions:
        new_script += script[last_end:start]
        new_text = talk_map[tidx].encode('utf-8') if tidx in talk_map else raw
        if bytes(c for c in raw if c < 0x20) != bytes(c for c in new_text if c < 0x20):
            new_text = raw  # bytes de controle sao codigo do script; nunca altera-los
        new_script += new_text
        diff = len(new_text) - len(raw)
        shifts.append((marker, end, shift, shift + diff))
        shift += diff
        last_end = end
    new_script += script[last_end:]

    markers = [x[0] for x in shifts]
    for fields in records:
        old = fields[12]
        if old >= len(script):
            continue  # nao e uma posicao no script (ex.: ultimo registro); nao mexer
        j = bisect.bisect_right(markers, old) - 1
        if j < 0:
            s = 0
        else:
            _, end_j, before, after = shifts[j]
            # ponteiro dentro do texto (alguns registros apontam para marcador+2): move junto com o inicio
            s = before if old < end_j else after
        fields[12] = old + s

    new_talk = bytearray(talk_data[:header_size])
    for fields in records:
        new_talk += struct.pack('<14I', *fields)
    new_talk += new_script

    new_size = len(new_talk)
    name_off = None
    for m in re.finditer(rb'talk\.dat', bytes(db_data[:3000])):
        name_off = m.start()
    struct.pack_into('<II', db_data, name_off - 8, talk_off, new_size)
    if new_size <= talk_size:
        db_data[talk_off:talk_off + new_size] = new_talk
        db_data[talk_off + new_size:talk_off + talk_size] = b'\x00' * (talk_size - new_size)
    else:
        db_data = db_data[:talk_off] + new_talk + db_data[talk_off + talk_size:]
        diff = new_size - talk_size
        for m in re.finditer(rb'([a-zA-Z_][a-zA-Z0-9_]{1,30})\.dat', bytes(db_data[:3000])):
            e = m.start() - 8
            f_off, _ = struct.unpack_from('<II', db_data, e)
            if f_off > talk_off:
                struct.pack_into('<I', db_data, e, f_off + diff)
    struct.pack_into('<I', db_data, 8, len(db_data))
    return bytes(db_data)


def iter_text_fields(db):
    """Gera (arquivo, registro, indice_campo, posicao, tamanho, texto)."""
    files = parse_nsac(db)
    for name, (rs, fields) in TEXT_FIELDS.items():
        off, _ = files[name]
        count = struct.unpack_from('<I', db, off)[0]
        for r in range(count):
            base = off + 4 + r * rs
            for k, (fo, fs) in enumerate(fields):
                pos = base + fo
                raw = db[pos:pos + fs]
                end = raw.find(b'\x00')
                yield name, r, k, pos, fs, raw[:end if end >= 0 else fs].decode('utf-8', 'replace')


def apply_fields(db, field_map):
    """field_map: {(arquivo, registro, indice_campo): texto}."""
    out = bytearray(db)
    for name, r, k, pos, fs, _ in iter_text_fields(db):
        t = field_map.get((name, r, k))
        if t is None:
            continue
        enc = t.encode('utf-8')
        if len(enc) > fs - 1:
            raise ValueError(f'texto longo demais em {name} reg {r}')
        out[pos:pos + fs] = enc + b'\x00' * (fs - len(enc))
    return bytes(out)


def apply_gamestring(gs, gs_map):
    """gs_map: {id_da_string: texto}."""
    count = struct.unpack_from('<I', gs, 0)[0]
    entries = []
    for i in range(count):
        sid, _, foff = struct.unpack_from('<III', gs, 4 + i * 12)
        end = gs.find(b'\x00', foff + 4)
        entries.append((sid, gs[foff:foff + 4], gs[foff + 4:end]))
    strings = bytearray()
    index = bytearray(struct.pack('<I', count))
    base = 4 + count * 12
    for sid, prefix, raw in entries:
        text = gs_map[sid] if sid in gs_map else raw.decode('utf-8', errors='replace')
        tb = text.encode('utf-8')
        index += struct.pack('<III', sid, len(text), base + len(strings))
        strings += prefix + tb + b'\x00'
    return bytes(index) + bytes(strings)
