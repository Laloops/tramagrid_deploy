import io
import base64
import string
from typing import TYPE_CHECKING
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from .session import TramaGridSession

def generate_grid(session: "TramaGridSession") -> None:
    """Gera a grade a partir da imagem original"""
    if not session.original:
        return

    img = session.original.copy()
    if session.posterize < 8:
        from PIL import ImageOps
        img = ImageOps.posterize(img, max(1, min(8, int(session.posterize))))

    if session.gamma != 1.0:
        img = img.point([int(((i / 255.0) ** (1.0 / session.gamma)) * 255) for i in range(256)] * 3)

    if session.saturation != 1.0:
        from PIL import ImageEnhance
        img = ImageEnhance.Color(img).enhance(session.saturation)

    if session.brightness != 1.0:
        from PIL import ImageEnhance
        img = ImageEnhance.Brightness(img).enhance(session.brightness)

    if session.contrast != 1.0:
        from PIL import ImageEnhance
        img = ImageEnhance.Contrast(img).enhance(session.contrast)

    ratio = session.gauge_stitches / max(1, session.gauge_rows)
    w, h = img.size
    new_w = max(10, session.grid_width_cells)
    new_h = int((h / w) * new_w * ratio)

    session.processed = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    session.quantized = session.processed.quantize(colors=session.max_colors, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)

    raw = session.quantized.getpalette()[:session.max_colors * 3]
    base = {}
    for i in range(session.max_colors):
        if i * 3 + 2 < len(raw):
            r, g, b = raw[i * 3:i * 3 + 3]
            base[i] = (r, g, b)
    session.palette = {i: session.custom_palette.get(i, c) for i, c in base.items()}
    draw_grid(session)

def draw_grid(session: "TramaGridSession") -> None:
    """Desenha a grade visual com otimização de performance"""
    if not session.quantized:
        return

    # Margens: Espaço para números em BAIXO e na DIREITA
    pad_top_left = 20
    pad_bot_right = 60

    wc, hc = session.quantized.size
    total_w = pad_top_left + wc * session.cell_size + pad_bot_right
    total_h = pad_top_left + hc * session.cell_size + pad_bot_right

    if not session.show_grid:
        base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
        # OTIMIZAÇÃO: Usa resize com NEAREST para criar imagem ampliada de uma vez
        prev = session.quantized.resize((wc * session.cell_size, hc * session.cell_size), Image.Resampling.NEAREST)
        base.paste(prev, (pad_top_left, pad_top_left))
        session.grid_image = base.convert("RGB")
        return

    # OTIMIZAÇÃO: Cria a imagem base ampliada de uma só vez em vez de loop aninhado
    # Primeiro, cria uma imagem RGB temporária com as cores da paleta
    temp_rgb = Image.new("RGB", (wc, hc))
    temp_draw = ImageDraw.Draw(temp_rgb)

    # Converte imagem indexada para RGB usando a paleta
    for y in range(hc):
        for x in range(wc):
            color_idx = session.quantized.getpixel((x, y))
            color = session.palette.get(color_idx, (255, 255, 255))
            temp_draw.point((x, y), color)

    # Agora amplia a imagem de uma só vez com NEAREST (muito mais rápido)
    base = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
    upscaled = temp_rgb.resize((wc * session.cell_size, hc * session.cell_size), Image.Resampling.NEAREST)
    base.paste(upscaled, (pad_top_left, pad_top_left))

    overlay = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
    d_ov = ImageDraw.Draw(overlay)

    # Linhas de Grade
    for y in range(hc + 1):
        py = pad_top_left + y * session.cell_size
        thk = (y % 10 == 0 or y == 0 or y == hc)
        d_ov.line([(pad_top_left, py), (pad_top_left + wc * session.cell_size, py)],
                  fill=(255, 255, 255, 180 if thk else 70), width=2 if thk else 1)
    for x in range(wc + 1):
        px = pad_top_left + x * session.cell_size
        thk = (x % 10 == 0 or x == 0 or x == wc)
        d_ov.line([(px, pad_top_left), (px, pad_top_left + hc * session.cell_size)],
                  fill=(255, 255, 255, 180 if thk else 70), width=2 if thk else 1)

    combined = Image.alpha_composite(base, overlay)
    d_comb = ImageDraw.Draw(combined)

    # Números da grade (padrão crochê/tapestry)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    except:
        try:
            font = ImageFont.truetype("liberation-sans-bold.ttf", 14)
        except:
            font = ImageFont.load_default()

    text_color = (100, 100, 100)

    # EIXO X (embaixo da grade): Direita → Esquerda (1 na direita, max na esquerda)
    y_pos_x = pad_top_left + hc * session.cell_size + 5
    for x in range(wc):
        num = wc - x  # inverte: x=0 vira wc, x=wc-1 vira 1
        txt = str(num)
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        tx = pad_top_left + x * session.cell_size + (session.cell_size - tw) / 2
        d_comb.text((tx, y_pos_x), txt, fill=text_color, font=font)

    # EIXO Y (lado DIREITO da grade): Baixo → Cima (1 embaixo, max em cima)
    x_pos_y = pad_top_left + wc * session.cell_size + 5  # 5px à direita da grade
    for y in range(hc):
        num = hc - y  # inverte: y=0 vira hc, y=hc-1 vira 1
        txt = str(num)
        bbox = draw.textbbox((0, 0), txt, font=font)
        th = bbox[3] - bbox[1]
        ty = pad_top_left + y * session.cell_size + (session.cell_size - th) / 2
        d_comb.text((x_pos_y, ty), txt, fill=text_color, font=font)

    session.grid_image = combined.convert("RGB")

def get_grid_base64(session: "TramaGridSession") -> str:
    """Retorna a grade como base64"""
    if not session.grid_image:
        return ""

    img = session.grid_image.copy()
    if session.highlighted_row >= 0:
        # Cria o overlay totalmente transparente (0 alpha)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)

        row_idx = session.quantized.height - session.highlighted_row
        if 0 <= row_idx < session.quantized.height:
            # pad_top_left é 20 no código
            py = 20 + row_idx * session.cell_size

            # Pinta o "escuro" APENAS acima e abaixo da linha,
            # deixando a linha com 0 alpha (cor original/branca)
            d.rectangle([0, 0, img.width, py], fill=(0, 0, 0, 180))
            d.rectangle([0, py + session.cell_size, img.width, img.height], fill=(0, 0, 0, 180))

        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()
