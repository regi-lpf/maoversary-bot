#!/usr/bin/env python3
"""Bot diário do Maoversary para o X (Twitter)."""

import argparse
import json
import math
import os
import random
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

MONTH_NAMES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "calendar_quotes.json"


def fc_match(pattern: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["fc-match", "-f", "%{file}", pattern],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        ).strip()
        if out and os.path.exists(out):
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def find_font_by_glob(keywords: list[str]) -> str | None:
    font_dirs = [Path("/usr/share/fonts"), Path.home() / ".local/share/fonts"]
    for base in font_dirs:
        if not base.exists():
            continue
        for ext in ("*.ttf", "*.otf"):
            for p in base.rglob(ext):
                name_l = p.name.lower()
                if all(k in name_l for k in keywords):
                    return str(p)
    return None


def find_font(candidates: list[str], fc_patterns: list[str], glob_keywords: list[list[str]], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue

    for pat in fc_patterns:
        matched = fc_match(pat)
        if matched:
            try:
                return ImageFont.truetype(matched, size=size)
            except OSError:
                continue

    for kw in glob_keywords:
        matched = find_font_by_glob(kw)
        if matched:
            try:
                return ImageFont.truetype(matched, size=size)
            except OSError:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def load_fonts(quote_size: int) -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    serif_regular = [
        "/usr/share/fonts/TTF/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/noto/NotoSerif-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "C:/Windows/Fonts/georgia.ttf",
    ]
    serif_bold = [
        "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/noto/NotoSerif-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "C:/Windows/Fonts/georgiab.ttf",
    ]
    serif_italic = [
        "/usr/share/fonts/TTF/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/noto/NotoSerif-Italic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        "C:/Windows/Fonts/georgiai.ttf",
    ]
    sans_bold = [
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    return {
        "title": find_font(serif_bold, ["DejaVu Serif:bold", "Liberation Serif:bold", "serif:bold"], [["serif", "bold"]], 34),
        "kicker": find_font(sans_bold, ["DejaVu Sans:bold", "Liberation Sans:bold", "sans:bold"], [["sans", "bold"]], 18),
        "badge": find_font(sans_bold, ["DejaVu Sans:bold", "Liberation Sans:bold", "sans:bold"], [["sans", "bold"]], 20),
        "meta": find_font(sans_bold, ["DejaVu Sans:bold", "Liberation Sans:bold", "sans:bold"], [["sans", "bold"]], 19),
        "chapter": find_font(sans_bold, ["DejaVu Sans:bold", "Liberation Sans:bold", "sans:bold"], [["sans", "bold"]], 22),
        "quote": find_font(serif_regular, ["DejaVu Serif:regular", "Liberation Serif:regular", "serif:regular"], [["serif", "regular"]], quote_size),
        "source": find_font(serif_italic, ["DejaVu Serif:italic", "Liberation Serif:italic", "serif:italic"], [["serif", "italic"]], 23),
        "seal": find_font(sans_bold, ["DejaVu Sans:bold", "Liberation Sans:bold", "sans:bold"], [["sans", "bold"]], 18),
    }


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_outer: float, r_inner: float, fill: str) -> None:
    pts = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    draw.polygon(pts, fill=fill)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    lines: list[str] = []
    for p_idx, para in enumerate(paragraphs):
        words = para.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) > max_width and current:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)
        if p_idx < len(paragraphs) - 1:
            lines.append("")
    return lines


def render_card_png(quote: dict, day: int, month: int, out_path: Path) -> Path:
    width = 1080
    card_x = 48
    card_w = width - card_x * 2
    inner_x = card_x + 44
    inner_w = card_w - 88
    month_name = MONTH_NAMES[month - 1]
    date_str = f"{day:02d} DE {month_name.upper()}"

    text_len = len(quote["text"])
    quote_size = 26 if text_len > 650 else (30 if text_len > 350 else 34)
    quote_line_h = int(quote_size * 1.55)
    fonts = load_fonts(quote_size)

    probe = Image.new("RGB", (width, 200))
    pdraw = ImageDraw.Draw(probe)

    quote_lines = wrap_text(pdraw, quote["text"], fonts["quote"], inner_w)
    source_lines = wrap_text(pdraw, f"— {quote['source']}", fonts["source"], inner_w - 130)
    chapter_lines = wrap_text(pdraw, quote["chapter"], fonts["chapter"], inner_w - 34)

    header_h = 210
    meta_h = 74
    chapter_h = len(chapter_lines) * 32 + 24
    body_h = sum(18 if l == "" else quote_line_h for l in quote_lines) + 28
    footer_card_h = max(100, len(source_lines) * 32 + 36)
    bottom_pad = 56
    height = max(960, header_h + 40 + meta_h + chapter_h + body_h + footer_card_h + bottom_pad + 48)

    img = Image.new("RGB", (width, height), "#e8dcc0")
    draw = ImageDraw.Draw(img)

    # Moldura externa do panfleto
    draw.rectangle([24, 24, width - 24, height - 24], fill="#f6eed9", outline="#7f1d1d", width=6)

    # Cabeçalho vermelho
    draw.rectangle([24, 24, width - 24, header_h], fill="#b91c1c")

    # Raios dourados sutis no cabeçalho
    cx, cy = width // 2, header_h
    r = 700
    for angle in range(-160, -19, 22):
        a1 = math.radians(angle)
        a2 = math.radians(angle + 10)
        pts = [
            (cx, cy),
            (max(24, min(width - 24, cx + math.cos(a1) * r)), max(24, cy + math.sin(a1) * r)),
            (max(24, min(width - 24, cx + math.cos(a2) * r)), max(24, cy + math.sin(a2) * r)),
        ]
        draw.polygon(pts, fill="#c9382b")

    # Faixa dourada
    draw.rectangle([24, header_h, width - 24, header_h + 6], fill="#eab308")

    # Estrela vetorial e título
    draw_star(draw, width / 2, 60, 16, 7, "#fde047")
    draw.text((width // 2, 114), "CITAÇÕES DO PRESIDENTE MAO ZEDONG", fill="#fbf7eb", font=fonts["title"], anchor="mm")
    draw.text((width // 2, 158), "EDIÇÃO POPULAR • LIVRO VERMELHO", fill="#fde047", font=fonts["kicker"], anchor="mm")

    # Cartão interno
    card_y = header_h + 40
    card_h = height - card_y - 64
    draw.rectangle([card_x + 10, card_y + 10, card_x + card_w + 10, card_y + card_h + 10], fill="#b91c1c")
    draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h], fill="#fffdf7", outline="#292524", width=3)

    # Badge de data
    badge_bbox = draw.textbbox((0, 0), date_str, font=fonts["badge"])
    badge_w = (badge_bbox[2] - badge_bbox[0]) + 36
    draw.rectangle([inner_x, card_y + 34, inner_x + badge_w, card_y + 74], fill="#b91c1c")
    draw.text((inner_x + 18, card_y + 54), date_str, fill="#fbf7eb", font=fonts["badge"], anchor="lm")

    # Número da citação
    draw.text((card_x + card_w - 44, card_y + 54), f"CITAÇÃO Nº {quote['id']} / 427", fill="#7f1d1d", font=fonts["meta"], anchor="rm")

    # Linha separadora vermelha
    draw.rectangle([inner_x, card_y + 92, inner_x + inner_w, card_y + 95], fill="#b91c1c")

    # Capítulo com estrela vetorial
    cur_y = card_y + 122
    draw_star(draw, inner_x + 10, cur_y + 12, 9, 4, "#b91c1c")
    for line in chapter_lines:
        draw.text((inner_x + 30, cur_y), line, fill="#b91c1c", font=fonts["chapter"])
        cur_y += 32
    cur_y += 14

    # Corpo da citação
    for line in quote_lines:
        if line == "":
            cur_y += 18
        else:
            draw.text((inner_x, cur_y), line, fill="#1c1917", font=fonts["quote"])
            cur_y += quote_line_h

    # Rodapé da fonte
    footer_y = card_y + card_h - footer_card_h - 22
    draw.rectangle([inner_x, footer_y, inner_x + inner_w, footer_y + 2], fill="#d6d3d1")

    src_y = footer_y + 22
    for line in source_lines:
        draw.text((inner_x, src_y), line, fill="#57534e", font=fonts["source"])
        src_y += 32

    # Carimbo vermelho
    seal_x = card_x + card_w - 128
    seal_y = footer_y + 20
    draw.rectangle([seal_x, seal_y, seal_x + 84, seal_y + 84], fill="#fbf2ef", outline="#b91c1c", width=4)
    draw.text((seal_x + 42, seal_y + 28), "語錄", fill="#b91c1c", font=fonts["seal"], anchor="mm")
    draw.text((seal_x + 42, seal_y + 56), str(quote.get("year") or "1966"), fill="#b91c1c", font=fonts["seal"], anchor="mm")

    img.save(out_path, format="PNG")
    return out_path


def build_tweet_text(quote: dict, day: int, month: int) -> str:
    month_name = MONTH_NAMES[month - 1]
    header = f"📅 {day:02d} de {month_name} — {quote['chapter']}"
    source = f"📖 {quote['source']}"
    full_text = f'"{quote["text"]}"'

    candidate = f"{header}\n\n{full_text}\n\n{source}"
    if len(candidate) <= 280:
        return candidate

    short_caption = f"{header}\n{source}\n\n#Maoversary #LivroVermelho"
    if len(short_caption) <= 280:
        return short_caption
    return f"{header}\n\n{source[:275 - len(header)]}..."


def post_to_x(text: str, image_path: Path) -> str:
    import tweepy

    api_key = os.environ["X_API_KEY"]
    api_secret = os.environ["X_API_SECRET"]
    access_token = os.environ["X_ACCESS_TOKEN"]
    access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"]

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)
    media = api_v1.media_upload(filename=str(image_path))

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
    )
    resp = client.create_tweet(text=text, media_ids=[media.media_id])
    return str(resp.data["id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Publica a citação do dia do Maoversary no X.")
    parser.add_argument("--date", help="Data no formato MM-DD (padrão: hoje em America/Sao_Paulo)")
    parser.add_argument("--dry-run", action="store_true", help="Gera o card e imprime o tweet sem publicar no X")
    parser.add_argument("--out", default="", help="Caminho opcional para salvar o PNG gerado")
    args = parser.parse_args()

    if args.date:
        month_s, day_s = args.date.split("-")
        month, day = int(month_s), int(day_s)
        key = f"{month:02d}-{day:02d}"
    else:
        now = datetime.now(ZoneInfo("America/Sao_Paulo"))
        month, day = now.month, now.day
        key = f"{month:02d}-{day:02d}"

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        calendar = json.load(f)

    quotes = calendar.get(key, [])
    if not quotes:
        raise SystemExit(f"Nenhuma citação encontrada para a data {key}.")

    quote = random.choice(quotes)
    tweet_text = build_tweet_text(quote, day, month)

    if args.out:
        out_path = Path(args.out)
        render_card_png(quote, day, month, out_path)
    else:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            out_path = Path(tmp.name)
        render_card_png(quote, day, month, out_path)

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"Data: {key} | Citação Nº {quote['id']}")
        print(f"Imagem gerada: {out_path}")
        print(f"Tweet ({len(tweet_text)} chars):\n{tweet_text}")
        return

    tweet_id = post_to_x(tweet_text, out_path)
    print(f"Publicado com sucesso! Tweet ID: {tweet_id}")


if __name__ == "__main__":
    main()
