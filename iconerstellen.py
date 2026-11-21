from PIL import Image

img = Image.open("icon_vorlage.png").convert("RGBA")
sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]

# Auf quadratischen Ausschnitt zentrieren, falls nötig
w, h = img.size
side = min(w, h)
left = (w - side) // 2
top = (h - side) // 2
square_img = img.crop((left, top, left + side, top + side))

square_img.save(
    "SokoIur.ico",
    format="ICO",
    sizes=sizes,
)
print("SokoIur.ico erfolgreich erstellt.")