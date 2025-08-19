from PIL import Image
import os

input_folder = "attachments"
output_folder = "images_thumbnails"

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(input_folder):
    if file.lower().endswith((".jpg", ".png", ".tiff", ".bmp", ".webp")):
        with Image.open(os.path.join(input_folder, file)) as img:
            # Make a copy so we don't modify the original object in place
            img_copy = img.copy()

            # Target size: original width/4, height/4
            target_size = (img.width // 4, img.height // 4)

            # This modifies the image in place, keeping aspect ratio
            img_copy.thumbnail(target_size, Image.LANCZOS)

            img_copy.save(os.path.join(output_folder, file))

        print(f"{file}: original {img.width}x{img.height} → thumbnail {img_copy.width}x{img_copy.height}")
