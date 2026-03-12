from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 627


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if bold:
        candidates.extend(
            [
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                r"C:\Windows\Fonts\segoeui.ttf",
                r"C:\Windows\Fonts\arial.ttf",
            ]
        )
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def vertical_gradient(draw: ImageDraw.ImageDraw, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(HEIGHT):
        t = y / max(HEIGHT - 1, 1)
        color = (lerp(top[0], bottom[0], t), lerp(top[1], bottom[1], t), lerp(top[2], bottom[2], t))
        draw.line([(0, y), (WIDTH, y)], fill=color)


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: tuple[int, int, int], text_color=(255, 255, 255)) -> None:
    font = load_font(24, bold=True)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    w = right - left + 40
    h = bottom - top + 20
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill)
    draw.text((x + 20, y + 9), text, font=font, fill=text_color)


def bar_chart(draw: ImageDraw.ImageDraw, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    draw.rounded_rectangle(area, radius=14, fill=(15, 24, 47))
    draw.text((x1 + 16, y1 + 12), "Produtividade semanal", font=load_font(17, bold=True), fill=(220, 233, 255))
    base = y2 - 22
    vals = [0.45, 0.72, 0.6, 0.82, 0.92, 0.76, 0.88]
    w = 14
    gap = 8
    start = x1 + 22
    for i, v in enumerate(vals):
        h = int((y2 - y1 - 60) * v)
        bx = start + i * (w + gap)
        by = base - h
        color = (58, 189, 161) if i >= 4 else (46, 127, 217)
        draw.rounded_rectangle((bx, by, bx + w, base), radius=5, fill=color)


def task_columns(draw: ImageDraw.ImageDraw, area: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = area
    draw.rounded_rectangle(area, radius=14, fill=(12, 20, 40))
    draw.text((x1 + 16, y1 + 12), "Kanban + Cronograma", font=load_font(17, bold=True), fill=(220, 233, 255))
    col_w = int((x2 - x1 - 52) / 3)
    titles = ["A Fazer", "Estudando", "Concluido"]
    for i, t in enumerate(titles):
        cx = x1 + 14 + i * (col_w + 12)
        cy = y1 + 40
        draw.rounded_rectangle((cx, cy, cx + col_w, y2 - 16), radius=10, fill=(20, 30, 56))
        draw.text((cx + 10, cy + 8), t, font=load_font(14, bold=True), fill=(177, 196, 228))
        card_h = 30
        yy = cy + 32
        for _ in range(3 if i != 1 else 2):
            draw.rounded_rectangle((cx + 10, yy, cx + col_w - 10, yy + card_h), radius=8, fill=(31, 43, 78))
            yy += 38


def build_cover(output_file: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 12, 24))
    draw = ImageDraw.Draw(img)

    vertical_gradient(draw, top=(10, 20, 45), bottom=(5, 72, 92))

    # Abstract background accents
    draw.ellipse((-130, -140, 280, 260), fill=(24, 54, 105))
    draw.ellipse((900, -110, 1330, 310), fill=(15, 96, 120))
    draw.ellipse((790, 430, 1320, 950), fill=(7, 58, 74))

    # Main left content block
    draw.rounded_rectangle((48, 56, 640, 570), radius=26, fill=(9, 17, 36))
    draw.text((84, 98), "Synex Study Flow", font=load_font(50, bold=True), fill=(235, 244, 255))
    draw.text((84, 168), "Sistema de gestao de estudos", font=load_font(28, bold=False), fill=(144, 194, 225))

    chip(draw, 84, 232, "Seguranca", (20, 122, 147))
    chip(draw, 84, 292, "Versatilidade", (31, 134, 95))
    chip(draw, 84, 352, "Projeto de Estudo", (36, 99, 180))

    bullets = [
        "Autenticacao, CSRF e validacoes por usuario",
        "Kanban, cronograma, metas e anotacoes",
        "Dashboard com metricas e foco em produtividade",
    ]
    y = 430
    for b in bullets:
        draw.ellipse((84, y + 10, 92, y + 18), fill=(94, 231, 198))
        draw.text((102, y), b, font=load_font(18), fill=(210, 226, 246))
        y += 38

    # Right app preview panel
    draw.rounded_rectangle((675, 74, 1148, 550), radius=28, fill=(8, 15, 32))
    draw.rounded_rectangle((695, 96, 1128, 130), radius=14, fill=(18, 30, 56))
    draw.ellipse((709, 107, 723, 121), fill=(255, 99, 99))
    draw.ellipse((729, 107, 743, 121), fill=(255, 199, 77))
    draw.ellipse((749, 107, 763, 121), fill=(82, 214, 129))
    draw.text((785, 103), "Dashboard | Cronograma | Kanban", font=load_font(16), fill=(184, 206, 236))

    bar_chart(draw, (695, 146, 928, 326))
    task_columns(draw, (940, 146, 1128, 326))
    task_columns(draw, (695, 338, 1128, 530))

    draw.text((70, 586), "Pronto para compartilhar no LinkedIn", font=load_font(16), fill=(155, 199, 214))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_file, format="PNG", optimize=True)


if __name__ == "__main__":
    output = Path("assets/linkedin/synex-linkedin-cover.png")
    build_cover(output)
    print(f"cover-generated: {output}")
