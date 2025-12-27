import io
import string
from datetime import datetime
from typing import TYPE_CHECKING
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader, simpleSplit

if TYPE_CHECKING:
    from .session import TramaGridSession

def export_png(session: "TramaGridSession"):
    """Exporta a grade como PNG"""
    if not session.grid_image:
        raise ValueError("Grade não gerada")

    buf = io.BytesIO()
    session.grid_image.save(buf, format="PNG")
    buf.seek(0)
    return buf

def export_pdf(session: "TramaGridSession", sid: str):
    """Exporta a grade como PDF"""
    if not session.grid_image:
        raise ValueError("Grade não gerada")

    is_landscape = session.grid_width_cells > session.quantized.height
    page_size = landscape(A4) if is_landscape else portrait(A4)
    pg_w, pg_h = page_size

    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=page_size)
    c.setTitle("Receita TramaGrid")

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, pg_h - 1.5 * cm, "TramaGrid")
    c.setFont("Helvetica", 9)
    info_text = f"Dim: {session.grid_width_cells}x{session.quantized.height} pts | Data: {datetime.now().strftime('%d/%m/%Y')}"
    if session.gauge_stitches and session.gauge_rows:
        cm_w = round(session.grid_width_cells * 10 / session.gauge_stitches, 1)
        cm_h = round(session.quantized.height * 10 / session.gauge_rows, 1)
        info_text += f" | Tam: {cm_w}x{cm_h}cm"
    c.drawRightString(pg_w - 1.5 * cm, pg_h - 1.5 * cm, info_text)

    # Grade
    grid_img = session.grid_image.copy()
    img_buffer = io.BytesIO()
    grid_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    avail_w, avail_h = pg_w - 2 * cm, pg_h - 4 * cm
    iw, ih = grid_img.size
    scale = min(avail_w / iw, avail_h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(ImageReader(img_buffer), (pg_w - dw) / 2, pg_h - 2.5 * cm - dh, width=dw, height=dh)

    # Legenda Compacta
    c.showPage()
    palette = session.get_palette_info()
    safe_symbols = string.ascii_uppercase + string.ascii_lowercase + "!@#$%&*?+-"
    symbol_map = {}

    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, pg_h - 2 * cm, "Legenda de Cores")
    c.setFont("Helvetica", 9)

    cols = 4 if is_landscape else 3
    col_width = (pg_w - 3 * cm) / cols
    row_height = 0.8 * cm
    start_y = pg_h - 3 * cm
    curr_x, curr_y = 1.5 * cm, start_y

    for i, color in enumerate(palette):
        sym = safe_symbols[i % len(safe_symbols)]
        symbol_map[color['index']] = sym
        c.setFillColor(HexColor(color['hex']))
        c.rect(curr_x, curr_y - 0.4 * cm, 0.4 * cm, 0.4 * cm, fill=1, stroke=1)
        c.setFillColor(HexColor("#000000"))
        c.drawString(curr_x + 0.6 * cm, curr_y - 0.3 * cm, f"{sym} : {color['hex']} ({color['count']} pts)")
        curr_x += col_width
        if (i + 1) % cols == 0:
            curr_x = 1.5 * cm
            curr_y -= row_height
        if curr_y < 2 * cm:
            c.showPage()
            curr_y = pg_h - 2 * cm
            curr_x = 1.5 * cm

    # Instruções (TABELA ZEBRADA + ZIGZAG)
    if curr_y > pg_h - 10 * cm:
        curr_y -= 1.5 * cm
    else:
        c.showPage()
        curr_y = pg_h - 2 * cm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(HexColor("#000000"))
    c.drawString(1.5 * cm, curr_y, "Instruções Linha a Linha")
    curr_y -= 1 * cm

    w, h = session.quantized.size
    available_text_width = pg_w - 3.5 * cm

    for row in range(h - 1, -1, -1):
        line = []
        current_idx = None
        count = 0

        # ZigZag:
        line_num = h - row
        is_odd_line = (line_num % 2 != 0)

        arrow = "←" if is_odd_line else "→"

        # Se Impar: D->E (Pixel Final -> Pixel 0)
        col_range = range(w - 1, -1, -1) if is_odd_line else range(w)

        for col in col_range:
            idx = session.quantized.getpixel((col, row))
            sym = symbol_map.get(idx, "?")
            if idx == current_idx:
                count += 1
            else:
                if current_idx is not None:
                    line.append(f"{count}x{sym}")
                current_idx = idx
                count = 1
        if current_idx is not None:
            line.append(f"{count}x{sym}")

        full_text = f"L{line_num} [{arrow}]:  " + "  ".join(line)

        lines = simpleSplit(full_text, "Helvetica", 9, available_text_width)
        row_height = (len(lines) * 0.5 * cm) + 0.2 * cm

        if curr_y - row_height < 1.5 * cm:
            c.showPage()
            curr_y = pg_h - 2 * cm

        if line_num % 2 == 1:
            c.setFillColor(HexColor("#F2F2F2"))
            c.rect(1.5 * cm, curr_y - row_height, pg_w - 3 * cm, row_height, fill=1, stroke=0)

        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.5)
        c.line(1.5 * cm, curr_y - row_height, pg_w - 1.5 * cm, curr_y - row_height)

        c.setFillColor(HexColor("#000000"))
        c.setFont("Helvetica", 9)
        text_y = curr_y - 0.4 * cm
        for txt_line in lines:
            c.drawString(1.7 * cm, text_y, txt_line)
            text_y -= 0.5 * cm

        curr_y -= row_height

    c.save()
    buffer.seek(0)
    return buffer
