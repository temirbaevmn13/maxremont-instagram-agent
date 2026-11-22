"""Бесплатная сборка типографических Reels, постов и Stories из текста."""
from __future__ import annotations
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NAVY = (12, 22, 36)
TEAL = (28, 218, 192)
WHITE = (246, 250, 252)
MUTED = (170, 192, 206)
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def wrapped(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_width: int):
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        line = ""
        for word in words:
            # Даже длинное слово не должно выходить за экран.
            parts = [word]
            while draw.textbbox((0, 0), parts[-1], font=f)[2] > max_width and len(parts[-1]) > 1:
                head = parts[-1]
                cut = len(head) - 1
                while cut > 1 and draw.textbbox((0, 0), head[:cut], font=f)[2] > max_width:
                    cut -= 1
                parts[-1:] = [head[:cut], head[cut:]]
            for part in parts:
                candidate = (line + " " + part).strip()
                if line and draw.textbbox((0, 0), candidate, font=f)[2] > max_width:
                    lines.append(line)
                    line = part
                else:
                    line = candidate
        lines.append(line)
    return lines


def draw_text(draw, txt, xy, f, fill, max_width, gap=16, max_lines=9):
    x, y = xy
    line_h = f.size + gap
    for line in wrapped(draw, txt, f, max_width)[:max_lines]:
        draw.text((x, y), line, font=f, fill=fill, stroke_width=0)
        y += line_h
    return y


def make_card(path: Path, heading: str, subtext: str, label: str, brand: str,
              dimensions=(W, H), accent=TEAL):
    w, h = dimensions
    im = Image.new("RGB", dimensions, NAVY)
    d = ImageDraw.Draw(im)
    # Ненавязчивый фон: декоративные фигуры, не выдаваемые за фото реальных работ.
    d.ellipse((w-460, -290, w+220, 390), outline=(26, 63, 75), width=14)
    d.ellipse((-420, h-580, 390, h+210), outline=(23, 67, 74), width=14)
    d.rounded_rectangle((65, 84, w-65, 102), radius=8, fill=accent)
    d.text((72, 160), label.upper()[:45], font=font(35, True), fill=accent)
    d.text((72, h-212), brand[:32], font=font(32, True), fill=MUTED)
    d.line((72, h-243, w-72, h-243), fill=(50, 88, 94), width=3)
    # Динамическое уменьшение шрифта при длинном заголовке.
    headline_size = 80 if h >= 1800 else 63
    while headline_size > 45:
        ff = font(headline_size, True)
        lines = wrapped(d, heading, ff, w-144)
        if len(lines) <= (5 if h >= 1800 else 3):
            break
        headline_size -= 5
    y = int(h * .28 if h >= 1800 else h * .24)
    y = draw_text(d, heading, (72, y), font(headline_size, True), WHITE, w-144, gap=17, max_lines=5)
    y += 60
    sub_size = 47 if h >= 1800 else 35
    draw_text(d, subtext, (72, y), font(sub_size), MUTED, w-144, gap=17, max_lines=6)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, quality=93)


def render(content: dict, brand: str, directory: Path, make_post: bool, kind: str = "all"):
    directory.mkdir(parents=True, exist_ok=True)
    panels = [
        (content["title"], "Три полезных шага"),
        ("Совет 1", content["tips"][0]),
        ("Совет 2", content["tips"][1]),
        ("Совет 3", content["tips"][2]),
        ("Нужна помощь?", content["cta"]),
    ]
    paths = {"reel": None, "story": None, "post": None}
    if kind in ("reel", "all"):
        frame_paths = []
        for i, (heading, sub) in enumerate(panels):
            p = directory / f"slide_{i+1:02}.png"
            make_card(p, heading, sub, f"{i+1} / 5 · полезные советы", brand)
            frame_paths.append(p)

    # 5 x 3 секунды = 15-секундный Reels (1080x1920, H.264 + AAC).
        manifest = directory / "frames.txt"
        with manifest.open("w", encoding="utf-8") as f:
            for p in frame_paths:
                f.write(f"file '{p.name}'\nduration 3\n")
            f.write(f"file '{frame_paths[-1].name}'\n")
        video = directory / "reel.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "concat", "-safe", "0", "-i", str(manifest),
           "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
           "-t", "15", "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
           "-movflags", "+faststart", "-shortest", str(video)]
        subprocess.run(cmd, check=True, timeout=180)
        paths["reel"] = video
    if kind in ("story", "all"):
        story = directory / "story.jpg"
        make_card(story, content["title"], content["tips"][0] + "\n\n" + content["cta"],
                  "СОВЕТ ДНЯ", brand)
        paths["story"] = story
    if make_post and kind in ("post", "all"):
        post = directory / "post.jpg"
        make_card(post, content["title"], "\n".join(content["tips"]),
                  "ПОЛЕЗНЫЙ ПОСТ", brand, dimensions=(1080, 1350))
        paths["post"] = post
    return paths
