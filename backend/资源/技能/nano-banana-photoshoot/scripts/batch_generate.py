#!/usr/bin/env python3
"""
Nano Banana 2 Photoshoot Batch Generator

Reads a spreadsheet (CSV/XLSX) of social media posts, generates structured
photo-shoot-quality prompts, fires them to Nano Banana 2 via API, and saves
organized outputs.

Usage:
    python batch_generate.py --input social_calendar.csv --output-dir ./output --api gemini
    python batch_generate.py --input social_calendar.csv --output-dir ./output --api fal

Environment Variables:
    GEMINI_API_KEY  - Required for --api gemini
    FAL_KEY         - Required for --api fal
"""

import argparse
import base64
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests --break-system-packages -q")
    import requests


# ---------------------------------------------------------------------------
# Platform -> aspect ratio mapping
# ---------------------------------------------------------------------------
PLATFORM_ASPECT = {
    "instagram": "1:1",
    "instagram_feed": "1:1",
    "instagram_story": "9:16",
    "instagram_stories": "9:16",
    "instagram_reels": "9:16",
    "reels": "9:16",
    "linkedin": "16:9",
    "twitter": "16:9",
    "x": "16:9",
    "facebook": "16:9",
    "facebook_feed": "16:9",
    "facebook_story": "9:16",
    "tiktok": "9:16",
    "youtube": "16:9",
    "youtube_shorts": "9:16",
    "pinterest": "2:3",
    "blog": "16:9",
    "website": "16:9",
    "email": "16:9",
}

# ---------------------------------------------------------------------------
# Quality anchors appended to every prompt
# ---------------------------------------------------------------------------
QUALITY_ANCHORS = (
    "professional photography, studio quality, sharp focus, high dynamic range, "
    "shot on Phase One IQ4 150MP, retouched, color-calibrated"
)

UNIVERSAL_NEGATIVES = (
    "watermark, text overlay, logo, signature, low resolution, blurry, noisy, "
    "overexposed, underexposed, artificial, stock photo, clipart, "
    "extra fingers, deformed hands, fused limbs, anatomical errors, "
    "uncanny valley, plastic skin"
)


def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filesystem-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    slug = slug.strip("-")[:max_len].rstrip("-")
    return slug or "image"


def detect_description_column(headers: list[str]) -> str | None:
    """Find the column most likely to contain image descriptions."""
    candidates = [
        "image_description", "image description", "visual_description",
        "visual description", "image_prompt", "image prompt", "prompt",
        "description", "visual", "image", "creative", "creative_brief",
        "creative brief", "image_brief", "image brief",
    ]
    lower_headers = [h.lower().strip() for h in headers]
    for c in candidates:
        if c in lower_headers:
            return headers[lower_headers.index(c)]
    return None


def detect_platform_column(headers: list[str]) -> str | None:
    candidates = ["platform", "channel", "network", "social_platform", "social platform"]
    lower_headers = [h.lower().strip() for h in headers]
    for c in candidates:
        if c in lower_headers:
            return headers[lower_headers.index(c)]
    return None


def detect_date_column(headers: list[str]) -> str | None:
    candidates = ["date", "publish_date", "publish date", "post_date", "post date", "scheduled_date"]
    lower_headers = [h.lower().strip() for h in headers]
    for c in candidates:
        if c in lower_headers:
            return headers[lower_headers.index(c)]
    return None


def read_spreadsheet(filepath: str) -> list[dict]:
    """Read CSV or XLSX into a list of dicts."""
    path = Path(filepath)
    if path.suffix.lower() in (".xlsx", ".xls"):
        try:
            import openpyxl
        except ImportError:
            os.system(f"{sys.executable} -m pip install openpyxl --break-system-packages -q")
            import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h or "").strip() for h in next(rows_iter)]
        data = []
        for row in rows_iter:
            d = {}
            for i, h in enumerate(headers):
                val = row[i] if i < len(row) else ""
                d[h] = str(val) if val is not None else ""
            data.append(d)
        wb.close()
        return data
    else:
        # CSV / TSV
        sep = "\t" if path.suffix.lower() == ".tsv" else ","
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=sep)
            return list(reader)


def build_structured_prompt(
    description: str,
    platform: str = "",
    topic: str = "",
    audience: str = "",
    caption: str = "",
) -> dict:
    """
    Build a structured JSON prompt from a plain-text description.
    This is the core prompt-engineering logic.
    """
    aspect_ratio = PLATFORM_ASPECT.get(
        platform.lower().strip().replace(" ", "_"), "16:9"
    )

    # Assemble the full prompt string
    parts = []

    # 1) Subject and scene from description
    parts.append(description.strip().rstrip("."))

    # 2) Context enrichment
    if topic:
        parts.append(f"themed around {topic}")
    if audience:
        parts.append(f"targeted at {audience}")

    # 3) Photography quality direction
    parts.append(QUALITY_ANCHORS)

    # 4) Negative prompt
    negative = UNIVERSAL_NEGATIVES

    assembled = ", ".join(parts) + f". Avoid: {negative}"

    prompt_json = {
        "subject": description,
        "scene": topic or "",
        "lighting": {
            "type": "natural + fill",
            "direction": "three-quarter front",
            "color_temperature": "5500K daylight",
            "modifiers": ["softbox diffused", "subtle rim light"]
        },
        "camera": {
            "angle": "eye level",
            "shot_type": "medium",
            "lens": "prime",
            "focal_length": "85mm",
            "aperture": "f/1.8",
            "depth_of_field": "shallow, subject isolated"
        },
        "composition": {
            "rule": "rule of thirds",
            "framing": "subject at right-third intersection",
            "foreground": "subtle blur element",
            "background": "complementary, out of focus",
            "negative_space": "leave room for text overlay if social"
        },
        "color_grading": {
            "palette": "brand-appropriate, balanced",
            "tone": "warm neutral",
            "contrast": "medium-high",
            "saturation": "natural, slightly enhanced"
        },
        "style": {
            "genre": "commercial photography",
            "mood": "confident, professional",
            "era": "contemporary",
            "reference": "high-end brand campaign",
            "texture": "clean with subtle grain"
        },
        "technical": {
            "aspect_ratio": aspect_ratio,
            "resolution": "2K",
            "format": "png"
        },
        "negative_prompt": negative,
        "assembled_prompt": assembled,
        "metadata": {
            "platform": platform,
            "topic": topic,
            "audience": audience,
            "caption_context": caption,
        }
    }

    return prompt_json


# ---------------------------------------------------------------------------
# API callers
# ---------------------------------------------------------------------------

def call_gemini_api(prompt: str, api_key: str) -> bytes | None:
    """Call the native Gemini API and return image bytes."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-3.1-flash-image-preview:generateContent"
    )
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # Extract image from response
    candidates = data.get("candidates", [])
    if not candidates:
        print("  WARNING: No candidates in Gemini response")
        return None

    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            b64 = part["inlineData"]["data"]
            return base64.b64decode(b64)

    print("  WARNING: No image data found in Gemini response")
    return None


def call_fal_api(prompt: str, aspect_ratio: str, resolution: str, fal_key: str) -> bytes | None:
    """Call the fal.ai REST API and return image bytes."""
    url = "https://queue.fal.run/fal-ai/nano-banana-2"
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "resolution": resolution,
        "thinking_level": "high",
        "num_images": 1,
        "limit_generations": True,
    }

    # Submit and poll
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    # fal.ai queue response may have images directly or a request_id to poll
    if "images" in result:
        image_url = result["images"][0]["url"]
        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()
        return img_resp.content

    # If queued, poll for result
    request_id = result.get("request_id")
    if request_id:
        status_url = f"https://queue.fal.run/fal-ai/nano-banana-2/requests/{request_id}/status"
        result_url = f"https://queue.fal.run/fal-ai/nano-banana-2/requests/{request_id}"

        for _ in range(60):  # max 5 minutes
            time.sleep(5)
            status_resp = requests.get(status_url, headers=headers, timeout=30)
            status_data = status_resp.json()
            if status_data.get("status") == "COMPLETED":
                result_resp = requests.get(result_url, headers=headers, timeout=30)
                result_data = result_resp.json()
                if "images" in result_data:
                    image_url = result_data["images"][0]["url"]
                    img_resp = requests.get(image_url, timeout=60)
                    img_resp.raise_for_status()
                    return img_resp.content
                break
            elif status_data.get("status") == "FAILED":
                print(f"  ERROR: fal.ai request failed: {status_data}")
                return None

    print("  WARNING: Could not retrieve image from fal.ai")
    return None


# ---------------------------------------------------------------------------
# Main batch processor
# ---------------------------------------------------------------------------

def process_batch(
    input_file: str,
    output_dir: str,
    api: str,
    resolution: str = "2K",
    rate_limit: int = 10,
    dry_run: bool = False,
):
    """Process a spreadsheet of posts and generate images."""

    # Validate API key
    if api == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key and not dry_run:
            print("ERROR: GEMINI_API_KEY environment variable not set")
            sys.exit(1)
    elif api == "fal":
        api_key = os.environ.get("FAL_KEY")
        if not api_key and not dry_run:
            print("ERROR: FAL_KEY environment variable not set")
            sys.exit(1)
    else:
        print(f"ERROR: Unknown API '{api}'. Use 'gemini' or 'fal'.")
        sys.exit(1)

    # Create output directories
    out = Path(output_dir)
    prompts_dir = out / "prompts"
    images_dir = out / "images"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Read input
    print(f"Reading {input_file}...")
    rows = read_spreadsheet(input_file)
    if not rows:
        print("ERROR: No data rows found in spreadsheet")
        sys.exit(1)

    headers = list(rows[0].keys())
    print(f"  Found {len(rows)} rows, columns: {headers}")

    # Detect columns
    desc_col = detect_description_column(headers)
    platform_col = detect_platform_column(headers)
    date_col = detect_date_column(headers)

    if not desc_col:
        print("ERROR: Could not detect image description column.")
        print(f"  Available columns: {headers}")
        print("  Expected one of: description, image_description, prompt, visual, creative")
        sys.exit(1)

    print(f"  Description column: '{desc_col}'")
    print(f"  Platform column: '{platform_col or 'not found (defaulting to 16:9)'}'")
    print(f"  Date column: '{date_col or 'not found (using today)'}'")

    # Process rows
    manifest = []
    delay = 60.0 / rate_limit  # seconds between requests

    for i, row in enumerate(rows):
        description = row.get(desc_col, "").strip()
        if not description:
            print(f"  Row {i+1}: Skipping (empty description)")
            continue

        platform = row.get(platform_col, "") if platform_col else ""
        date_str = row.get(date_col, "") if date_col else ""

        # Normalize date
        if date_str:
            try:
                dt = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                date_str = datetime.now().strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Context columns
        topic = row.get("topic", "") or row.get("Theme", "") or ""
        audience = row.get("audience", "") or row.get("Audience", "") or ""
        caption = row.get("caption", "") or row.get("Caption", "") or row.get("copy", "") or ""

        # Build prompt
        prompt_json = build_structured_prompt(
            description=description,
            platform=platform,
            topic=topic,
            audience=audience,
            caption=caption,
        )

        slug = slugify(description)
        platform_slug = slugify(platform) if platform else "general"
        filename_base = f"{date_str}_{platform_slug}_{slug}"

        # Save prompt JSON
        prompt_path = prompts_dir / f"{filename_base}.json"
        with open(prompt_path, "w") as f:
            json.dump(prompt_json, f, indent=2)

        print(f"  Row {i+1}/{len(rows)}: {filename_base}")
        print(f"    Prompt saved: {prompt_path}")

        image_path = images_dir / f"{filename_base}.png"
        status = "prompt_only"

        if not dry_run:
            try:
                assembled = prompt_json["assembled_prompt"]
                if api == "gemini":
                    img_bytes = call_gemini_api(assembled, api_key)
                else:
                    aspect = prompt_json["technical"]["aspect_ratio"]
                    img_bytes = call_fal_api(assembled, aspect, resolution, api_key)

                if img_bytes:
                    with open(image_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"    Image saved: {image_path} ({len(img_bytes)} bytes)")
                    status = "complete"
                else:
                    status = "api_error"
            except Exception as e:
                print(f"    ERROR: {e}")
                status = "error"

            # Rate limit
            if i < len(rows) - 1:
                time.sleep(delay)
        else:
            status = "dry_run"

        manifest.append({
            "row_number": i + 1,
            "date": date_str,
            "platform": platform,
            "description": description[:100],
            "prompt_file": str(prompt_path),
            "image_file": str(image_path),
            "aspect_ratio": prompt_json["technical"]["aspect_ratio"],
            "resolution": resolution,
            "status": status,
        })

    # Write manifest
    manifest_path = out / "manifest.csv"
    if manifest:
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=manifest[0].keys())
            writer.writeheader()
            writer.writerows(manifest)
        print(f"\nManifest saved: {manifest_path}")

    # Summary
    total = len(manifest)
    complete = sum(1 for m in manifest if m["status"] == "complete")
    errors = sum(1 for m in manifest if "error" in m["status"])
    print(f"\nDone! {complete}/{total} images generated, {errors} errors")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nano Banana 2 Batch Image Generator")
    parser.add_argument("--input", required=True, help="Path to CSV/XLSX file")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--api", choices=["gemini", "fal"], default="gemini",
                        help="Which API backend to use")
    parser.add_argument("--resolution", default="2K",
                        choices=["0.5K", "1K", "2K", "4K"],
                        help="Image resolution (fal.ai only)")
    parser.add_argument("--rate-limit", type=int, default=10,
                        help="Max requests per minute")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate prompts only, skip API calls")

    args = parser.parse_args()
    process_batch(
        input_file=args.input,
        output_dir=args.output_dir,
        api=args.api,
        resolution=args.resolution,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run,
    )
