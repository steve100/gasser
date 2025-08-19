#!/usr/bin/env python3
import os
import json
import time
import argparse
import csv
from typing import Any, Dict, List, Optional

# PyExifTool wrapper (pip name: PyExifTool)
import exiftool
import requests

# ---- Default configuration ----
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
    try:
        if isinstance(val, list) and val:
            val = val[0]
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

def read_exif_with_pyexiftool(et: exiftool.ExifTool, file_path: str) -> Dict[str, Any]:
    """
    Use PyExifTool's low-level API (execute).
    Returns a dict of tags for one file (or {} if none).
    Handles both bytes and str returns.
    """
    # -G keeps group (EXIF:..., File:...), -j outputs JSON, -n for numeric (no rational formatting)
    raw = et.execute(b"-G", b"-j", b"-n", file_path.encode("utf-8"))
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="replace")
    else:
        text = raw  # already a str on some platforms
    try:
        arr = json.loads(text)
        return arr[0] if arr else {}
    except json.JSONDecodeError:
        # Fall back: try without -G in case some exiftool builds behave oddly
        raw2 = et.execute(b"-j", b"-n", file_path.encode("utf-8"))
        text2 = raw2.decode("utf-8", errors="replace") if isinstance(raw2, bytes) else raw2
        arr2 = json.loads(text2)
        return arr2[0] if arr2 else {}

def main():
    ap = argparse.ArgumentParser(description="Extract image EXIF to JSON+CSV with fixed lat/lng + reverse geocoding (PyExifTool .execute).")
    ap.add_argument("--folder", default="./attachments", help="Folder containing images")
    ap.add_argument("--json-out", default="image_metadata_full.json", help="Output JSON file")
    ap.add_argument("--csv-out", default="image_metadata_full.csv", help="Output CSV file")
    ap.add_argument("--jsonl", default=None, help="Optional JSON Lines file (one JSON object per line)")
    ap.add_argument("--email", default="your_email@example.com", help="Contact email for Nominatim User-Agent")
    ap.add_argument("--rate-sec", type=float, default=1.0, help="Delay between reverse geocode calls (seconds)")
    ap.add_argument("--no-geo", action="store_true", help="Skip reverse geocoding (still fixes lat/lng)")
    ap.add_argument("--verbose", "-v", action="store_true", help="Print extra info")
    args = ap.parse_args()

    if args.verbose:
        print(f"Working dir: {os.getcwd()}")
        print(f"Folder: {os.path.abspath(args.folder)}")
        print(f"JSON output: {os.path.abspath(args.json_out)}")
        print(f"CSV output:  {os.path.abspath(args.csv_out)}")
        if args.jsonl:
            print(f"JSONL:       {os.path.abspath(args.jsonl)}")

    files = collect_files(args.folder, DEFAULT_IMAGE_EXTENSIONS)
    if not files:
        print(f"⚠️  No images found in {args.folder} with extensions {DEFAULT_IMAGE_EXTENSIONS}")
        return

    if args.verbose:
        print(f"Found {len(files)} files:")
        for p in files[:10]:
            print("  -", p)
        if len(files) > 10:
            print(f"  ...and {len(files)-10} more")

    records: List[Dict[str, Any]] = []
    jsonl_fp = open(args.jsonl, "w", encoding="utf-8") if args.jsonl else None

    try:
        with exiftool.ExifTool() as et, open(args.csv_out, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            header = [simplify_key(tag) for tag in DEFAULT_FIELDS] + ["GPSLatitudeFixed", "GPSLongitudeFixed", "Location", "FilePath"]
            writer.writerow(header)

            for file_path in files:
                data = read_exif_with_pyexiftool(et, file_path)

                rec: Dict[str, Any] = {}
                rec["FilePath"] = file_path

                lat_ref = data.get("EXIF:GPSLatitudeRef") or data.get("GPSLatitudeRef")
                lon_ref = data.get("EXIF:GPSLongitudeRef") or data.get("GPSLongitudeRef")
                raw_lat = data.get("EXIF:GPSLatitude") or data.get("GPSLatitude")
                raw_lon = data.get("EXIF:GPSLongitude") or data.get("GPSLongitude")

                # Copy requested fields (prefer EXIF: prefix but accept bare tags too)
                for tag in DEFAULT_FIELDS:
                    val = data.get(tag)
                    if val is None:
                        plain = tag.split(":", 1)[-1]
                        val = data.get(plain, "N/A")
                    rec[simplify_key(tag)] = val

                # Fix lat/lon signs using refs
                gps_lat = safe_float(raw_lat)
                gps_lon = safe_float(raw_lon)
                if gps_lat is not None and isinstance(lat_ref, str):
                    gps_lat = -abs(gps_lat) if lat_ref.strip().upper() == "S" else abs(gps_lat)
                if gps_lon is not None and isinstance(lon_ref, str):
                    gps_lon = -abs(gps_lon) if lon_ref.strip().upper() == "W" else abs(gps_lon)

                rec["GPSLatitudeFixed"] = gps_lat if gps_lat is not None else None
                rec["GPSLongitudeFixed"] = gps_lon if gps_lon is not None else None

                # Reverse geocode if enabled and coords exist
                if (not args.no_geo) and (gps_lat is not None) and (gps_lon is not None):
                    rec["Location"] = reverse_geocode(gps_lat, gps_lon, args.email)
                    time.sleep(max(args.rate_sec, 0))
                else:
                    rec["Location"] = "No GPS data"

                # CSV row
                writer.writerow([rec[simplify_key(tag)] for tag in DEFAULT_FIELDS] +
                                [rec["GPSLatitudeFixed"], rec["GPSLongitudeFixed"], rec["Location"], rec["FilePath"]])

                # JSON aggregate
                records.append(rec)

                # Optional JSONL
                if jsonl_fp:
                    jsonl_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")

                if args.verbose:
                    print(f"Processed: {os.path.basename(file_path)}")

    finally:
        if jsonl_fp:
            jsonl_fp.close()

    # Save JSON atomically
    tmp_path = args.json_out + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, args.json_out)

    print(f"\n✅ Done. Saved {len(records)} records to:")
    print(f"   JSON: {args.json_out}")
    print(f"   CSV:  {args.csv_out}")
    if args.jsonl:
        print(f"   JSONL: {args.jsonl}")

if __name__ == "__main__":
    main()
