import math
from collections import defaultdict
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from .session import TramaGridSession

def get_palette_info(session: "TramaGridSession") -> List[Dict]:
    """Retorna informações de todas as cores da paleta"""
    if not session.palette:
        return []

    # Conta o uso de pixels de forma eficiente
    usage = defaultdict(int)
    if session.quantized:
        w, h = session.quantized.size
        for y in range(h):
            for x in range(w):
                usage[session.quantized.getpixel((x, y))] += 1

    result = []
    # Itera sobre self.palette para garantir que cores novas apareçam
    for idx, rgb in session.palette.items():
        r, g, b = rgb
        result.append({
            "index": idx,
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "count": usage.get(idx, 0)  # Se não tiver na grade, o uso é 0
        })

    # Ordena pelas mais usadas para facilitar o trabalho
    return sorted(result, key=lambda x: -x['count'])

def replace_color(session: "TramaGridSession", idx, hex_val):
    """Substitui uma cor na paleta"""
    session._save_state()
    session.custom_palette[idx] = session.palette[idx] = (
        int(hex_val[1:3], 16),
        int(hex_val[3:5], 16),
        int(hex_val[5:7], 16)
    )
    session._draw_grid()

def merge_colors(session: "TramaGridSession", f, t):
    """Mescla uma cor com outra"""
    if not session.quantized:
        return

    session._save_state()

    # Substitui a cor 'f' pela 't' instantaneamente
    table = []
    for i in range(256):
        table.append(t if i == f else i)
    session.quantized = session.quantized.point(table)

    # Remove a cor antiga da paleta
    session.palette.pop(f, None)
    session.custom_palette.pop(f, None)
    session._draw_grid()

def merge_many_colors(session: "TramaGridSession", from_list, to_index):
    """Mescla múltiplas cores em uma única"""
    if not session.quantized:
        return

    session._save_state()

    # Cria uma tabela de substituição única para TODAS as cores
    table = []
    for i in range(256):
        if i in from_list:
            table.append(to_index)  # Se for uma das cores ruins, vira a cor boa
        else:
            table.append(i)         # Senão, mantém

    # Aplica a troca instantaneamente em C (super rápido)
    session.quantized = session.quantized.point(table)

    # Remove as cores antigas da paleta
    for idx in from_list:
        if idx != to_index:  # Proteção extra
            session.palette.pop(idx, None)
            session.custom_palette.pop(idx, None)

    session._draw_grid()

def delete_color(session: "TramaGridSession", idx):
    """Deleta uma cor da paleta"""
    if not session.quantized:
        return

    session._save_state()

    # Encontra a cor mais próxima para substituir (para não deixar buracos pretos)
    c1 = session.palette.get(idx)
    if not c1:
        return  # Se a cor já não existe, sai

    best, min_d = None, float('inf')
    for i, c2 in session.palette.items():
        if i == idx:
            continue
        # Distância Euclidiana simples
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))
        if d < min_d:
            min_d, best = d, i

    # Se achou uma cor substituta, aplica a troca rápida
    if best is not None:
        table = []
        for i in range(256):
            table.append(best if i == idx else i)
        session.quantized = session.quantized.point(table)

    # Remove a cor deletada
    session.palette.pop(idx, None)
    session.custom_palette.pop(idx, None)
    session._draw_grid()

def add_color_to_palette(session: "TramaGridSession", hex_val: str):
    """Adiciona uma nova cor à paleta"""
    if not hex_val or len(hex_val) != 7 or hex_val[0] != '#':
        raise ValueError("Hex inválido")

    try:
        rgb = (int(hex_val[1:3], 16), int(hex_val[3:5], 16), int(hex_val[5:7], 16))
    except:
        raise ValueError("Cor inválida")

    # Se a cor já existe, retorna o índice dela
    for idx, color in session.palette.items():
        if color == rgb:
            return idx

    # Limpeza e expansão automática
    if len(session.palette) >= session.max_colors:
        # Primeiro, remove cores não usadas (limpeza)
        if session.quantized:
            used = set(c[1] for c in session.quantized.getcolors(maxcolors=1000))
            session.palette = {k: v for k, v in session.palette.items() if k in used}
            session.custom_palette = {k: v for k, v in session.custom_palette.items() if k in used}

        # Se mesmo limpando ainda estiver cheio, aumenta o limite (teto 256)
        if len(session.palette) >= session.max_colors:
            if session.max_colors < 256:
                session.max_colors = min(256, session.max_colors + 16)
            else:
                raise ValueError("Limite máximo de 256 cores atingido.")

    # Adiciona a nova cor em um índice livre
    new_idx = 0
    while new_idx in session.palette:
        new_idx += 1

    session.palette[new_idx] = session.custom_palette[new_idx] = rgb
    return new_idx

def suggest_clusters(session: "TramaGridSession", threshold=50.0):
    """Sugere clusters de cores similares"""
    if not session.palette:
        return []

    colors = list(session.palette.items())
    groups = []
    visited = set()

    for i in range(len(colors)):
        idx1, rgb1 = colors[i]
        if idx1 in visited:
            continue
        grp = [idx1]
        for j in range(i + 1, len(colors)):
            idx2, rgb2 = colors[j]
            if idx2 in visited:
                continue
            if math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2))) < threshold:
                grp.append(idx2)
                visited.add(idx2)
        if len(grp) > 1:
            visited.add(idx1)
            groups.append(grp)

    return groups
