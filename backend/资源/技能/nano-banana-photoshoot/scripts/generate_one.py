#!/usr/bin/env python3
"""
Nano Banana 2 Single Image Generator

Takes a plain-text prompt, rewrites it as a structured photoshoot-quality
prompt, fires it to Nano Banana 2, and saves the result.

Usage:
    python generate_one.py "A detective in a rainy alley at night" --api gemini
    python generate_one.py "Product shot of wireless earbuds" --api fal --resolution 4K
    python generate_one.py "CEO portrait for LinkedIn" --platform linkedin --api gemini

Environment Variables:
    GEMINI_API_KEY  - Required for --api gemini
    FAL_KEY         - Required for --api fal
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Import from batch_generate (same directory)
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from batch_generate import (
    build_structured_prompt,
    call_gemini_api,
    call_fal_api,
    slugify,
    PLATFORM_ASPECT,
)


def main():
    parser = argparse.ArgumentParser(description="Generate a single photoshoot-quality image")
    parser.add_argument("prompt", help="Plain-English image description")
    parser.add_argument("--api", choices=["gemini", "fal"], default="gemini")
    parser.add_argument("--platform", default="", help="Target platform (instagram, linkedin, etc.)")
    parser.add_argument("--resolution", default="2K", choices=["0.5K", "1K", "2K", "4K"])
    parser.add_argument("--output-dir", default="./output")
    parser.add_argument("--dry-run", action="store_true", help="Just generate the prompt, skip API call")

    args = parser.parse_args()

    # Build structured prompt
    prompt_json = build_structured_prompt(
        description=args.prompt,
        platform=args.platform,
    )

    # File naming
    date_str = datetime.now().strftime("%Y-%m-%d")
    slug = slugify(args.prompt)
    platform_slug = slugify(args.platform) if args.platform else "general"
    filename_base = f"{date_str}_{platform_slug}_{slug}"

    out = Path(args.output_dir)
    prompts_dir = out / "prompts"
    images_dir = out / "images"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Save prompt
    prompt_path = prompts_dir / f"{filename_base}.json"
    with open(prompt_path, "w") as f:
        json.dump(prompt_json, f, indent=2)

    print("=" * 60)
    print("STRUCTURED PROMPT")
    print("=" * 60)
    print(json.dumps(prompt_json, indent=2))
    print()
    print("=" * 60)
    print("ASSEMBLED PROMPT (sent to API)")
    print("=" * 60)
    print(prompt_json["assembled_prompt"])
    print()
    print(f"Prompt saved: {prompt_path}")

    if args.dry_run:
        print("\n[DRY RUN] Skipping API call.")
        return

    # Call API
    assembled = prompt_json["assembled_prompt"]
    api_key = None

    if args.api == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: Set GEMINI_API_KEY environment variable")
            sys.exit(1)
        print(f"\nCalling Gemini API (gemini-3.1-flash-image-preview)...")
        img_bytes = call_gemini_api(assembled, api_key)
    else:
        api_key = os.environ.get("FAL_KEY")
        if not api_key:
            print("ERROR: Set FAL_KEY environment variable")
            sys.exit(1)
        aspect = prompt_json["technical"]["aspect_ratio"]
        print(f"\nCalling fal.ai API (nano-banana-2, {aspect}, {args.resolution})...")
        img_bytes = call_fal_api(assembled, aspect, args.resolution, api_key)

    if img_bytes:
        image_path = images_dir / f"{filename_base}.png"
        with open(image_path, "wb") as f:
            f.write(img_bytes)
        print(f"Image saved: {image_path} ({len(img_bytes):,} bytes)")
    else:
        print("ERROR: No image returned from API")
        sys.exit(1)


if __name__ == "__main__":
    main()
