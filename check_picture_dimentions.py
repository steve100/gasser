from PIL import Image
import os

folder = "attachments"
for file in os.listdir(folder):
    if file.lower().endswith((".jpg", ".png", ".tiff", ".bmp", ".webp")):
        with Image.open(os.path.join(folder, file)) as img:
            w, h = img.size
        print(f"{file}: {w} x {h}")
