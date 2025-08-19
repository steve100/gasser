
from PIL import Image
import math
import os
from pathlib import Path
import argparse
import csv

# Try to import tiktoken; if unavailable, use a simple fallback heuristic
try:
    import tiktoken
    def count_tokens(text: str, model: str = "gpt-4o") -> int:
        try:
            enc = tiktoken.encoding_for_model(model)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    TOKENIZER_NAME = "tiktoken"
except Exception:
    def count_tokens(text: str, model: str = "gpt-4o") -> int:
        # Fallback: rough heuristic ~4 chars per token
        return max(1, math.ceil(len(text) / 4))
    TOKENIZER_NAME = "heuristic(4 chars/token)"

PRICES = {
    "gpt-4o": {
        "image_per_mp": 0.005,       # $ per megapixel
        "input_per_1k": 0.0025,      # $ per 1K input tokens
        "output_per_1k": 0.010       # $ per 1K output tokens
    },
    "gpt-4o-mini": {
        "image_per_mp": 0.0004,      # $ per megapixel
        "input_per_1k": 0.00015,     # $ per 1K input tokens
        "output_per_1k": 0.00060     # $ per 1K output tokens
    }
}

MIN_MP = 0.1
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

def billable_mp(width: int, height: int) -> tuple[float, float]:
    total_pixels = width * height
    megapixels = total_pixels / 1_000_000
    rounded = max(MIN_MP, math.ceil(megapixels * 10) / 10)
    return megapixels, rounded

def iter_images(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            yield p

def main():
    ap = argparse.ArgumentParser(description="Batch image cost estimator for GPT-4o and GPT-4o-mini")
    ap.add_argument("image_dir", help="Directory containing images (searched recursively)")
    ap.add_argument("prompt_file", help="Text file containing the prompt to send with each image")
    ap.add_argument("--output-tokens", type=int, default=0, help="Expected output tokens per image (default: 0)")
    ap.add_argument("--csv", default="image_cost_report.csv", help="Path to write CSV report")
    args = ap.parse_args()

    image_dir = Path(args.image_dir)
    if not image_dir.exists():
        raise SystemExit(f"Image directory not found: {image_dir}")

    try:
        prompt_text = Path(args.prompt_file).read_text(encoding="utf-8")
    except Exception as e:
        raise SystemExit(f"Failed to read prompt file: {e}")

    input_tokens = count_tokens(prompt_text, "gpt-4o")
    output_tokens = max(0, int(args.output_tokens))

    rows = []
    totals = {
        "count": 0,
        "gpt-4o": {"image": 0.0, "input": 0.0, "output": 0.0, "total": 0.0},
        "gpt-4o-mini": {"image": 0.0, "input": 0.0, "output": 0.0, "total": 0.0},
    }

    images = list(iter_images(image_dir))
    if not images:
        raise SystemExit(f"No supported images found in: {image_dir}")

    for img_path in images:
        with Image.open(img_path) as im:
            w, h = im.size
        mp, bill_mp = billable_mp(w, h)

        # Costs common token portions (same for every image since one prompt per image)
        for model, p in PRICES.items():
            image_cost = bill_mp * p["image_per_mp"]
            input_cost = (input_tokens / 1000) * p["input_per_1k"]
            output_cost = (output_tokens / 1000) * p["output_per_1k"]
            total_cost = image_cost + input_cost + output_cost

            rows.append({
                "image": str(img_path),
                "width": w,
                "height": h,
                "megapixels": round(mp, 3),
                "billable_mp": round(bill_mp, 1),
                "model": model,
                "image_cost": round(image_cost, 6),
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
            })

            totals[model]["image"] += image_cost
            totals[model]["input"] += input_cost
            totals[model]["output"] += output_cost
            totals[model]["total"] += total_cost

        totals["count"] += 1

    # Write CSV
    csv_path = Path(args.csv)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)

    # Print summary
    print(f"\nTokenizer: {TOKENIZER_NAME}")
    print(f"Images processed: {totals['count']}")
    print(f"Prompt tokens (input): {input_tokens}")
    print(f"Output tokens (per image): {output_tokens}\n")

    for model in ["gpt-4o", "gpt-4o-mini"]:
        t = totals[model]
        print(f"{model}:")
        print(f"  Image cost total : ${t['image']:.6f}")
        print(f"  Input cost total : ${t['input']:.6f}")
        print(f"  Output cost total: ${t['output']:.6f}")
        print(f"  GRAND TOTAL      : ${t['total']:.6f}\n")

    print(f"CSV report written to: {csv_path.resolve()}")

if __name__ == "__main__":
    main()
