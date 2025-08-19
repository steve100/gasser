#!/usr/bin/env python3
import os
import json
import time
import argparse
from typing import Any, Dict, List, Optional

import exiftool
import requests

# ---- Default configuration (can be overridden by CLI) ----
DEFAULT_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".heic", ".png")
DEFAULT_FIELDS = [
    "File:FileName",
    "EXIF:DateTimeOriginal",
    "EXIF:Make",
    "EXIF:Model",
    "EXIF:LensModel",
    "EXIF:ISO",
    "EXIF:ShutterSpeedValue",
    "EXIF:ApertureValue",
    "EXIF:FocalLength",
    "EXIF:ImageWidth",
    "EXIF:ImageHeight",
    "EXIF:GPSLongitudeRef",
    "EXIF:GPSLatitudeRef",
    "EXIF:GPSLatitude",
    "EXIF:GPSLongitude",
]

def reverse_geocode(lat: float, lon: float, user_agent_email: str, timeout: int = 10) -> str:
    """Reverse geocode using OpenStreetMap Nominatim."""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
    headers = {"User-Agent": f"ExifLocationApp/1.0 ({user_agent_email})"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            return data.get("display_name", "N/A")
        else:
            return f"N/A (HTTP {r.status_code})"
    except Exception as e:
        return f"N/A ({e})"

def safe_float(val: Any) -> Optional[float]:
    """Convert EXIFTool values to float safely (handles lists)."""
    try:
        if isinstance(val, list) and val:
            val = val[0]
        # EXIFTool may return strings like "37 deg 46' 30.00\" N"
        # but usually returns decimal; let float() try; if it fails, return None.
        return float(val)
    except Exception:
        return None

def collect_files(folder: str, extensions: tuple) -> List[str]:
    files = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and name.lower().endswith(extensions):
            files.append(p)
    files.sort()
    return files

def simplify_key(tag: str) -> str:
    return tag.split(":")[-1]

def main():
    ap = argparse.ArgumentParser(description="Extract image EXIF to JSON with fixed lat/lng + reverse geocoding.")
    ap.add_argument("--folder", default="./images", help="Folder containing images")
    ap.add_argument("--out", default="image_metadata_full.json", help="Output JSON file")
    ap.add_argument("--jsonl", default=None, help="Optional JSON Lines file (one JSON per line)")
    ap.add_argument("--email", default="your_email@example.com", help="Contact email for Nominatim User-Agent")
    ap.add_argument("--rate-sec", type=float, default=1.0, help="Delay between reverse geocode calls (seconds)")
    ap.add_argument("--no-geo", action="store_true", help="Skip reverse geocoding (still fixes lat/lng)")
    args = ap.parse_args()

    files = collect_files(args.folder, DEFAULT_IMAGE_EXTENSIONS)
    if not files:
        print(f"⚠️  No images found in {args.folder} with extensions {DEFAULT_IMAGE_EXTENSIONS}")
        return

    print(f"Found {len(files)} files. Reading EXIF with exiftool…")

    records: List[Dict[str, Any]] = []
    jsonl_fp = open(args.jsonl, "w", encoding="utf-8") if args.jsonl else None

    try:
        with exiftool.ExifTool() as et:
            metadata_batch = et.get_metadata_batch(files)

            for data in metadata_batch:
                rec: Dict[str, Any] = {}
                # include absolute path for convenience
                rec["FilePath"] = data.get("SourceFile", "")

                # Gather requested fields + compute fixed lat/lng
                lat_ref = data.get("EXIF:GPSLatitudeRef")
                lon_ref = data.get("EXIF:GPSLongitudeRef")
                raw_lat = data.get("EXIF:GPSLatitude")
                raw_lon = data.get("EXIF:GPSLongitude")

                for tag in DEFAULT_FIELDS:
                    rec[simplify_key(tag)] = data.get(tag, "N/A")

                # Fix lat/lng signs using refs, if numeric
                gps_lat = safe_float(raw_lat)
                gps_lon = safe_float(raw_lon)
                if gps_lat is not None and isinstance(lat_ref, str):
                    if lat_ref.upper().strip() == "S":
                        gps_lat = -abs(gps_lat)
                    else:
                        gps_lat = abs(gps_lat)
                if gps_lon is not None and isinstance(lon_ref, str):
                    if lon_ref.upper().strip() == "W":
                        gps_lon = -abs(gps_lon)
                    else:
                        gps_lon = abs(gps_lon)

                # Store both raw and fixed for transparency
                rec["GPSLatitudeFixed"] = gps_lat if gps_lat is not None else None
                rec["GPSLongitudeFixed"] = gps_lon if gps_lon is not None else None

                # Reverse geocode if both present
                if not args.no-geo and gps_lat is not None and gps_lon is not None:
                    location = reverse_geocode(gps_lat, gps_lon, args.email)
                    rec["Location"] = location
                    # Be nice to Nominatim (free, rate-limited)
                    time.sleep(max(args.rate_sec, 0))
                else:
                    rec["Location"] = "No GPS data"

                records.append(rec)
                if jsonl_fp:
                    jsonl_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")

                print(f"Processed: {os.path.basename(rec.get('FilePath',''))}")

    finally:
        if jsonl_fp:
            jsonl_fp.close()

    # Write a single pretty JSON array
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Saved {len(records)} records to: {args.out}")
    if args.jsonl:
        print(f"   Also wrote JSON Lines to: {args.jsonl}")

if __name__ == "__main__":
    main()
