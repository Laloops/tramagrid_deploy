import io
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from .session import TramaGridSession

def load_image(session: "TramaGridSession", file_bytes: bytes) -> None:
    """Carrega uma imagem na sessão"""
    from PIL import Image
    session.original = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    session.history = []

def paint_cell(session: "TramaGridSession", x, y, idx):
    """Pinta uma célula específica"""
    if not session.quantized or idx not in session.palette:
        return

    session._save_state()
    if 0 <= x < session.quantized.width and 0 <= y < session.quantized.height:
        session.quantized.putpixel((x, y), idx)
        session._draw_grid()

def get_pixel_index(session: "TramaGridSession", x, y):
    """Retorna o índice da cor de um pixel"""
    return int(session.quantized.getpixel((x, y))) if session.quantized and 0 <= x < session.quantized.width and 0 <= y < session.quantized.height else -1

def replace_index_in_region(session: "TramaGridSession", x, y, w, h, f, t):
    """Substitui um índice por outro em uma região"""
    if not session.quantized:
        return

    session._save_state()
    for py in range(max(0, y), min(session.quantized.height, y + h)):
        for px in range(max(0, x), min(session.quantized.width, x + w)):
            if session.quantized.getpixel((px, py)) == f:
                session.quantized.putpixel((px, py), t)
    session._draw_grid()

def get_row_summary(session: "TramaGridSession", row_num: int) -> Dict:
    """Retorna um resumo de uma linha específica"""
    if not session.quantized:
        return {"summary": []}

    w, h = session.quantized.size
    # Converte o número da carreira (1...H) para o índice da imagem (H-1...0)
    img_row = h - row_num
    if img_row < 0 or img_row >= h:
        return {"summary": []}

    summary = []
    curr_idx = None
    count = 0

    # ZigZag: Linhas ímpares (←), Linhas pares (→)
    col_range = range(w - 1, -1, -1) if row_num % 2 != 0 else range(w)

    for x in col_range:
        idx = session.quantized.getpixel((x, img_row))
        if idx == curr_idx:
            count += 1
        else:
            if curr_idx is not None:
                r, g, b = session.palette[curr_idx]
                summary.append({"count": count, "hex": f"#{r:02x}{g:02x}{b:02x}"})
            curr_idx, count = idx, 1

    if curr_idx is not None:
        r, g, b = session.palette[curr_idx]
        summary.append({"count": count, "hex": f"#{r:02x}{g:02x}{b:02x}"})

    return {"summary": summary}
