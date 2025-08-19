
#!/usr/bin/env python3
"""
llm_gauge_extractor.py (JSON-first version)
------------------------------------------
- Sends ALL images in a directory to an OpenAI vision model
- Requests a STRICT JSON response first; falls back to text parsing if needed
- Normalizes blank numeric fields to "0"
- Prints from normalized JSON and writes JSON to disk

Usage:
  python llm_gauge_extractor.py --dir images_thumbnails --json-out results_llm.json --model gpt-4o-mini [--no-pretty]
"""
import argparse
import base64
import json
import os
import re
from io import BytesIO
from typing import Dict, List, Optional

from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI, BadRequestError

VALID_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4o-mini-audio-preview",
    "gpt-4o-audio-preview"
}

MODEL_DEFAULT = "gpt-4o-mini"
DEFAULT_DIR = "images_thumbnails"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

PROMPT_JSON = """You will receive a set of images with their file names.
Identify the SINGLE best Odometer image (trip meter top, total mileage bottom) and the SINGLE best Gas Pump image (dollars top, gallons bottom).
Return ONLY valid JSON with this structure:

{
  "odometer_image": {
    "file": "<filename or 'not found'>",
    "top_value_trip": "<string or ''>",
    "bottom_value_total_mileage": "<string or ''>"
  },
  "gas_pump_image": {
    "file": "<filename or 'not found'>",
    "top_value_dollars": "<string or ''>",
    "bottom_value_gallons": "<string or ''>"
  }
}

Rules:
- Do not include any extra fields or commentary.
- Use the provided file names exactly as given.
- If an image type is not found, set "file" to "not found" and leave its values as "".
"""

PROMPT_FALLBACK_TEXT = """You will receive a set of images (filenames are provided).

Your task:
- Identify the SINGLE best Odometer Image (if any). An odometer image shows two numeric values:
  a top value (trip meter) and a bottom value (total mileage).
- Identify the SINGLE best Gas Pump Image (if any). A gas pump image shows two numeric values:
  a top value in dollars and a bottom value in gallons.

Output EXACTLY the two labeled sections below. If one type is not present, write "not found" for its file name
and leave values blank.

Odometer Image
File name: <best-odometer-file-or 'not found'>
Top value (trip meter): <value or ''>
Bottom value (total mileage): <value or ''>

Gas Pump Image
File name: <best-gas-pump-file-or 'not found'>
Top value (dollars): <value or ''>
Bottom value (gallons): <value or ''>
"""

def encode_image_as_jpeg_data_uri(path: str) -> str:
    with Image.open(path) as im:
        im = im.convert("RGB")
        buf = BytesIO()
        im.save(buf, format="JPEG", quality=95)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def list_images(dir_path: str) -> List[str]:
    if not os.path.isdir(dir_path):
        raise SystemExit(f"ERROR: Directory not found: {dir_path}")
    files = []
    for name in sorted(os.listdir(dir_path)):
        ext = os.path.splitext(name)[1].lower()
        if ext in IMAGE_EXTS:
            files.append(os.path.join(dir_path, name))
    if not files:
        raise SystemExit(f"ERROR: No image files found in {dir_path} (extensions: {', '.join(sorted(IMAGE_EXTS))})")
    return files

def build_user_content(image_paths: List[str], prompt_text: str):
    listing = "\n".join(f"- {os.path.basename(p)}" for p in image_paths)
    content = [
        {"type": "text", "text": prompt_text + "\n\nHere are the files:\n" + listing + "\n"}
    ]
    for p in image_paths:
        uri = encode_image_as_jpeg_data_uri(p)
        content.append({"type": "image_url", "image_url": {"url": uri, "detail": "high"}})
    return content

def call_openai_json_first(image_paths: List[str], model: str) -> Dict:
    client = OpenAI()

    # 1) Try strict JSON mode
    try:
        msgs = [
            {"role": "system", "content": "You are a precise vision assistant."},
            {"role": "user", "content": build_user_content(image_paths, PROMPT_JSON)},
        ]
        resp = client.chat.completions.create(
            model=model,
            messages=msgs,
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        txt = resp.choices[0].message.content.strip()
        data = json.loads(txt)
        return data
    except BadRequestError:
        # Some models may not support response_format; fall through to text mode.
        pass
    except Exception:
        # If JSON parse fails for any reason, fall back to text mode.
        pass

    # 2) Fallback: get text, then parse with regex
    msgs = [
        {"role": "system", "content": "You are a precise vision assistant. Follow the user's formatting exactly."},
        {"role": "user", "content": build_user_content(image_paths, PROMPT_FALLBACK_TEXT)},
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        temperature=0.0,
        max_tokens=900,
    )
    text = resp.choices[0].message.content.strip()
    parsed = extract_json_from_text(text)
    parsed["raw_text"] = text
    return parsed

def extract_json_from_text(text: str) -> Dict[str, Dict[str, Optional[str]]]:
    t = text.replace('\r\n', '\n').replace('\r', '\n')

    # Make patterns more flexible across whitespace and punctuation variations
    def find(section_name, label):
        # Build a regex that finds a label after the section header, allowing extra whitespace
        pattern = rf"{section_name}\s+.*?{label}\s*:\s*(.+)"
        m = re.search(pattern, t, flags=re.IGNORECASE | re.DOTALL)
        if not m:
            return None
        # Take only up to end of line
        return m.group(1).splitlines()[0].strip()

    odo_file = find(r"Odometer\s+Image", r"File\s+name")
    odo_top  = find(r"Odometer\s+Image", r"Top\s+value\s*\(trip\s*meter\)")
    odo_bot  = find(r"Odometer\s+Image", r"Bottom\s+value\s*\(total\s*mileage\)")

    pump_file = find(r"Gas\s+Pump\s+Image", r"File\s+name")
    pump_top  = find(r"Gas\s+Pump\s+Image", r"Top\s+value\s*\(dollars\)")
    pump_bot  = find(r"Gas\s+Pump\s+Image", r"Bottom\s+value\s*\(gallons\)")

    return {
        "odometer_image": {
            "file": odo_file,
            "top_value_trip": odo_top,
            "bottom_value_total_mileage": odo_bot,
        },
        "gas_pump_image": {
            "file": pump_file,
            "top_value_dollars": pump_top,
            "bottom_value_gallons": pump_bot,
        },
    }

def zero_if_blank(v: Optional[str]) -> str:
    return "0" if (v is None or str(v).strip() == "") else str(v)

def normalize_data(data: Dict) -> Dict:
    # Ensure keys exist
    data.setdefault("odometer_image", {})
    data.setdefault("gas_pump_image", {})
    # Normalize numeric fields
    data["odometer_image"]["top_value_trip"] = zero_if_blank(data["odometer_image"].get("top_value_trip"))
    data["odometer_image"]["bottom_value_total_mileage"] = zero_if_blank(data["odometer_image"].get("bottom_value_total_mileage"))
    data["gas_pump_image"]["top_value_dollars"] = zero_if_blank(data["gas_pump_image"].get("top_value_dollars"))
    data["gas_pump_image"]["bottom_value_gallons"] = zero_if_blank(data["gas_pump_image"].get("bottom_value_gallons"))
    # Default file names if missing
    data["odometer_image"]["file"] = data["odometer_image"].get("file") or "not found"
    data["gas_pump_image"]["file"] = data["gas_pump_image"].get("file") or "not found"
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DEFAULT_DIR, help=f"Directory of images (default: {DEFAULT_DIR})")
    ap.add_argument("--json-out", default="results_llm.json", help="Path to write JSON output")
    ap.add_argument("--model", default=MODEL_DEFAULT, help=f"Vision model to use (default: {MODEL_DEFAULT})")
    ap.add_argument("--no-pretty", action="store_true", help="Do not print the human-readable sections to stdout")
    args = ap.parse_args()

    # Validate model
    if args.model not in VALID_MODELS:
        raise SystemExit(f"ERROR: Invalid model '{args.model}'. Valid options are: {', '.join(sorted(VALID_MODELS))}")

    # Load API key
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("ERROR: OPENAI_API_KEY not found. Put it in a .env file or set the environment variable.")

    # Gather images
    image_paths = list_images(args.dir)

    # Call LLM (JSON-first)
    data = call_openai_json_first(image_paths, args.model)

    # Attach metadata
    data["input_files"] = [os.path.basename(p) for p in image_paths]
    data["model"] = args.model
    data["source_dir"] = os.path.abspath(args.dir)

    # Normalize blanks -> "0"
    data = normalize_data(data)

    # Pretty print from normalized data
    if not args.no_pretty:
        print("Odometer Image")
        print(f"File name: {data['odometer_image']['file']}")
        print(f"Top value (trip meter): {data['odometer_image']['top_value_trip']}")
        print(f"Bottom value (total mileage): {data['odometer_image']['bottom_value_total_mileage']}")
        print()
        print("Gas Pump Image")
        print(f"File name: {data['gas_pump_image']['file']}")
        print(f"Top value (dollars): {data['gas_pump_image']['top_value_dollars']}")
        print(f"Bottom value (gallons): {data['gas_pump_image']['bottom_value_gallons']}")

    # Save JSON
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nWrote JSON to {args.json_out}")

if __name__ == "__main__":
    main()
