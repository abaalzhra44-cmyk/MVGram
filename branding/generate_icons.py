#!/usr/bin/env python3
"""Regenerate MVGram Android launcher artwork from the editable SVG masters.
Run from any working directory: python3 branding/generate_icons.py
Requires CairoSVG and Pillow. No Gradle task or Android build is invoked.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import cairosvg
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "TMessagesProj/src/main/res"
BRAND = ROOT / "branding"
NAVY = "#101C36"
WHITE = "#F7FAFF"

# Raster legacy launcher sizes, and Android adaptive foreground canvas sizes.
DENSITY = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
LAUNCHER = {k: int(48*v) for k, v in DENSITY.items()}
FOREGROUND = {k: int(108*v) for k, v in DENSITY.items()}
ICON_FILE = re.compile(r"^(?:ic_launcher(?:_round)?|icon(?:_[2-6])?_(?:launcher(?:_round)?|foreground(?:_round)?(?:_sa)?))\.png$")
BG_FILE = re.compile(r"^icon(?:_[2-6])?_background(?:_round|_clip(?:_round)?|_sa)?\.png$")

master = (BRAND / "mvgram-icon.svg").read_bytes()
foreground = (BRAND / "mvgram-foreground.svg").read_bytes()
for folder in sorted(PROJECT.glob("mipmap-*")):
    density = folder.name.removeprefix("mipmap-")
    if density not in DENSITY:
        continue
    for dest in folder.glob("*.png"):
        name = dest.name
        if ICON_FILE.match(name):
            px = FOREGROUND[density] if "foreground" in name else LAUNCHER[density]
            is_round = "round" in name
            svg = foreground if "foreground" in name else master
            out = Image.open(BytesIO(cairosvg.svg2png(bytestring=svg, output_width=px, output_height=px))).convert("RGBA")
            if is_round:
                mask = Image.new("L", (px, px), 0)
                from PIL import ImageDraw
                ImageDraw.Draw(mask).ellipse((0, 0, px-1, px-1), fill=255)
                out.putalpha(Image.composite(out.getchannel("A"), Image.new("L", (px, px), 0), mask))
            out.save(dest, format="PNG", optimize=True)
        elif BG_FILE.match(name):
            px = FOREGROUND[density]
            if "clip" in name:
                Image.new("RGBA", (px, px), (0, 0, 0, 0)).save(dest, format="PNG", optimize=True)
            else:
                Image.new("RGBA", (px, px), (16, 28, 54, 255)).save(dest, format="PNG", optimize=True)

# Standalone/SMS distribution keeps independently packaged icon resources.
standalone = ROOT / "TMessagesProj_AppStandalone/src/main/res"
for folder in sorted(standalone.glob("mipmap-*")):
    density = folder.name.removeprefix("mipmap-")
    if density not in DENSITY:
        continue
    for dest in folder.glob("icon_[2-6]_launcher_sa.png"):
        px = LAUNCHER[density]
        image = Image.open(BytesIO(cairosvg.svg2png(bytestring=master, output_width=px, output_height=px))).convert("RGBA")
        image.save(dest, format="PNG", optimize=True)

# Legacy draggable launcher artwork (.webp), rasterized from the same master.
for folder in sorted(PROJECT.glob("drawable-*dpi")):
    dest = folder / "ic_launcher_dr.webp"
    if dest.exists():
        density = folder.name.removeprefix("drawable-").removesuffix("dpi")
        d = {"m": "mdpi", "h": "hdpi", "x": "xhdpi", "xx": "xxhdpi", "xxx": "xxxhdpi"}.get(density)
        if d:
            px = LAUNCHER[d]
            image = Image.open(BytesIO(cairosvg.svg2png(bytestring=master, output_width=px, output_height=px))).convert("RGBA")
            image.save(dest, format="WEBP", quality=100, lossless=True)

# Replace only icon background-layer XML resources; keep all resource IDs stable.
for path in (PROJECT / "drawable").glob("icon*background*.xml"):
    name = path.stem
    if not re.fullmatch(r"icon(?:_[2-6])?_background(?:_round|_sa)?", name):
        continue
    path.write_text(f'''<?xml version="1.0" encoding="utf-8"?>\n<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">\n    <solid android:color="{NAVY}" />\n</shape>\n''', encoding="utf-8")

# Monochrome Android themed icon: single-color speech mark, no text/details.
mono = f'''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="432" android:viewportHeight="432">\n    <path android:fillColor="{WHITE}" android:pathData="M216,76 C134,76 68,132 68,201 C68,248 99,290 146,311 L132,364 C130,371 138,377 145,373 L208,335 C211,335 214,336 216,336 C298,336 364,280 364,211 C364,142 298,76 216,76 Z" />\n</vector>\n'''
(PROJECT / "drawable/mvgram_monochrome_icon.xml").write_text(mono, encoding="utf-8")

# Keep Android's existing splash resource ID/API and supply an MVGram mark.
splash = f'''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="320dp" android:height="320dp" android:viewportWidth="432" android:viewportHeight="432">\n    <path android:fillColor="{WHITE}" android:pathData="M216,76 C134,76 68,132 68,201 C68,248 99,290 146,311 L132,364 C130,371 138,377 145,373 L208,335 C211,335 214,336 216,336 C298,336 364,280 364,211 C364,142 298,76 216,76 Z" />\n    <path android:fillColor="{NAVY}" android:pathData="M154,178h124a10,10 0,0 1,0 20h-124a10,10 0,0 1,0 -20z M154,222h78a10,10 0,0 1,0 20h-78a10,10 0,0 1,0 -20z" />\n</vector>\n'''
(PROJECT / "drawable/mvgram_splash_320.xml").write_text(splash, encoding="utf-8")

# Keep the splash mark legible in both light and night app themes.
for style_file in (PROJECT / "values-night/styles.xml", PROJECT / "values-v31/styles.xml"):
    if style_file.exists():
        style_text = style_file.read_text(encoding="utf-8")
        style_text = re.sub(r'(<item name="android:windowSplashScreenBackground">).*?(</item>)',
                            rf'\1{NAVY}\2', style_text)
        style_file.write_text(style_text, encoding="utf-8")

# Establish one shared deep-navy adaptive-icon background; preserve XML IDs.
for p in sorted((PROJECT / "drawable").glob("icon*background*.xml")):
    if re.fullmatch(r"icon(?:_[2-6])?_background(?:_round|_sa)?", p.stem):
        continue
    # Leave non-background drawables untouched.

# Update display names in all shipped locale resource files without rewriting XML formatting.
for path in sorted(PROJECT.glob("values*/strings.xml")):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'(<string\s+name="AppName">).*?(</string>)', r'\1MVGram\2', text)
    text = re.sub(r'(<string\s+name="AppNameBeta">).*?(</string>)', r'\1MVGram Beta\2', text)
    # About/settings version row: localize the app brand but retain translated wording.
    def version_brand(m):
        body = m.group(2)
        body = re.sub(r"(?i)telegram|تيليجرام|텔레그램", "MVGram", body, count=1)
        return m.group(1) + body + m.group(3)
    text = re.sub(r'(<string\s+name="TelegramVersion">)(.*?)(</string>)', version_brand, text)
    # This text describes the app itself (not Telegram's service/protocol).
    def language_brand(m):
        body = re.sub(r"(?i)telegram", "MVGram", m.group(2), count=1)
        body = body.replace("تيليجرام", "MVGram").replace("텔레그램", "MVGram")
        return m.group(1) + body + m.group(3)
    text = re.sub(r'(<string\s+name="LanguageUnknownCustomAlert">)(.*?)(</string>)', language_brand, text)
    path.write_text(text, encoding="utf-8")

# Shared monochrome identity mark for small app/message notifications.
notification = f'''<?xml version="1.0" encoding="utf-8"?>\n<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="24dp" android:height="24dp" android:viewportWidth="432" android:viewportHeight="432">\n    <path android:fillColor="{WHITE}" android:pathData="M216,76 C134,76 68,132 68,201 C68,248 99,290 146,311 L132,364 C130,371 138,377 145,373 L208,335 C211,335 214,336 216,336 C298,336 364,280 364,211 C364,142 298,76 216,76 Z" />\n</vector>\n'''
(PROJECT / "drawable/mvgram_notification.xml").write_text(notification, encoding="utf-8")
for old_icon in PROJECT.glob("drawable-*dpi/notification.webp"):
    old_icon.unlink()

# Application ID is shared by standard, Huawei, standalone and test app variants.
props = ROOT / "gradle.properties"
ptext = props.read_text(encoding="utf-8")
ptext, n = re.subn(r"(?m)^APP_PACKAGE=.*$", "APP_PACKAGE=com.mvgram.messenger", ptext)
if n != 1:
    raise RuntimeError(f"Expected one APP_PACKAGE setting; found {n}")
props.write_text(ptext, encoding="utf-8")
print("Generated launcher/adaptive/round/standalone assets and updated selected app branding.")
