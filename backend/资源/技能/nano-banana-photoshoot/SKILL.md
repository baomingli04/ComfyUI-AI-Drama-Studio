---
name: nano-banana-photoshoot
description: >
  Generate professional photo-shoot-quality images using Nano Banana 2 (Gemini 3.1 Flash Image).
  Takes plain-English image descriptions and rewrites them as structured JSON prompts with
  cinematic lighting, camera settings, composition, color grading, style direction, and negative
  prompts. Then fires the prompt to Nano Banana 2 via API and saves both the prompt JSON and
  the output image in organized folders. Use this skill whenever someone asks to generate images,
  create social media visuals, produce marketing photography, build a batch of images from a
  spreadsheet, create product shots, lifestyle photography, event promo images, or any task
  involving AI image generation with Nano Banana, Nano Banana 2, or Gemini image models.
  Also trigger when the user mentions "image prompt", "photo prompt", "structured prompt",
  "prompt engineering for images", or wants to process a spreadsheet/CSV of posts into images.
---

# Nano Banana 2 Photoshoot Prompt Engine

Turn plain-English image descriptions into structured, cinematic-quality prompts and generate
images via the Nano Banana 2 API. Every output should look like it came from a professional
photo shoot with intentional lighting, lens choice, and art direction.

## Quick Start

1. Read the user's plain-text description
2. Rewrite it as a structured JSON prompt (see Prompt Schema below)
3. Fire it to the Nano Banana 2 API
4. Save the prompt JSON + downloaded image in organized folders

## API Configuration

This skill supports two API backends. Check which one the user has configured:

### Option A: Google Gemini API (native, recommended)

Environment variable: `GEMINI_API_KEY`

```bash
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "ASSEMBLED_PROMPT_HERE"}]}]
  }'
```

The response contains `candidates[0].content.parts[]`. Look for parts where `inlineData` is
present. The image is base64-encoded in `inlineData.data` with MIME type in `inlineData.mimeType`.

### Option B: fal.ai API

Environment variable: `FAL_KEY`

```bash
# Install once
npm install --save @fal-ai/client
```

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("fal-ai/nano-banana-2", {
  input: {
    prompt: "ASSEMBLED_PROMPT_HERE",
    aspect_ratio: "16:9",   // or 1:1, 9:16, 3:2, 4:3, etc.
    output_format: "png",
    resolution: "2K",        // 0.5K, 1K, 2K, 4K
    thinking_level: "high",  // better prompt adherence
    num_images: 1
  }
});
// result.data.images[0].url  -> download URL
```

### Option C: Direct REST (fal.ai, no SDK)

```bash
curl -X POST "https://queue.fal.run/fal-ai/nano-banana-2" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "ASSEMBLED_PROMPT_HERE",
    "aspect_ratio": "16:9",
    "output_format": "png",
    "resolution": "2K",
    "thinking_level": "high",
    "num_images": 1
  }'
```

---

## Prompt Schema

When the user gives you a plain-text description, rewrite it into this JSON structure.
This is your internal working format. The final prompt sent to the API is assembled
from these fields into a single string.

```json
{
  "subject": "",
  "scene": "",
  "lighting": {
    "type": "",
    "direction": "",
    "color_temperature": "",
    "modifiers": []
  },
  "camera": {
    "angle": "",
    "shot_type": "",
    "lens": "",
    "focal_length": "",
    "aperture": "",
    "depth_of_field": ""
  },
  "composition": {
    "rule": "",
    "framing": "",
    "foreground": "",
    "background": "",
    "negative_space": ""
  },
  "color_grading": {
    "palette": "",
    "tone": "",
    "contrast": "",
    "saturation": ""
  },
  "style": {
    "genre": "",
    "mood": "",
    "era": "",
    "reference": "",
    "texture": ""
  },
  "technical": {
    "aspect_ratio": "",
    "resolution": "",
    "format": ""
  },
  "negative_prompt": "",
  "assembled_prompt": ""
}
```

## Prompt Assembly Rules

Build the `assembled_prompt` by concatenating fields into a single, dense, comma-separated
string. This is what gets sent to Nano Banana 2. Order matters for emphasis.

**Assembly order:**

1. Subject and action (most important, goes first)
2. Scene/environment
3. Camera: shot type, angle, lens, focal length, aperture, depth of field
4. Lighting: type, direction, color temperature, modifiers
5. Composition: rule, framing, foreground/background treatment
6. Color grading: palette, tone, contrast, saturation
7. Style: genre, mood, era, texture
8. Technical quality tags
9. Negative prompt appended as: "Avoid: [negative prompt terms]"

**Quality anchors to always include** (append these to every assembled prompt):

```
professional photography, studio quality, sharp focus, high dynamic range,
shot on Phase One IQ4 150MP, retouched, color-calibrated
```

**Example transform:**

User says:
> "A detective in a rainy alley at night"

Assembled prompt:
> "A hardboiled detective in a long trench coat standing in a rain-soaked alley,
> wet cobblestones reflecting neon signs, shot from low angle, 35mm lens f/1.4,
> shallow depth of field, dramatic chiaroscuro lighting from a single overhead
> streetlamp, cool blue and amber color palette with crushed blacks, high contrast,
> desaturated midtones, film noir mood, 1940s aesthetic, grain texture,
> professional photography, studio quality, sharp focus, high dynamic range,
> shot on Phase One IQ4 150MP, retouched, color-calibrated.
> Avoid: cartoon, illustration, watermark, text overlay, low resolution, blurry,
> oversaturated, flat lighting, stock photo feel"

---

## Lighting Reference Library

Use these as building blocks. Mix and match based on the subject.

| Style | Description | Best For |
|---|---|---|
| Rembrandt | Single source, 45-degree angle, triangle of light on shadow side of face | Portraits, moody headshots |
| Butterfly / Paramount | Light directly above and in front of subject, creates butterfly shadow under nose | Beauty, fashion, glamour |
| Split | Light hitting exactly one half of the face | Drama, editorial, contrast |
| Rim / Edge | Light from behind outlining the subject | Silhouettes, product separation |
| Golden Hour | Warm, low-angle natural light (sun 15 degrees above horizon) | Lifestyle, outdoor, warmth |
| Blue Hour | Cool ambient light, post-sunset pre-dark | Moody exteriors, cityscapes |
| Hard Flash | Direct, on-camera flash, harsh shadows | Editorial fashion, Terry Richardson style |
| Softbox Diffused | Large soft source, minimal shadows | Product, beauty, e-commerce |
| Practical Lighting | Using visible light sources in scene (lamps, screens, candles) | Interior lifestyle, cozy scenes |
| Volumetric | Visible light rays through atmosphere (fog, dust, haze) | Cinematic, epic, atmospheric |

## Camera/Lens Reference

| Lens | Focal Length | Aperture | Effect | Best For |
|---|---|---|---|---|
| Ultra-wide | 14-24mm | f/2.8 | Dramatic perspective, environmental context | Architecture, landscapes, immersive |
| Wide | 24-35mm | f/1.4-2.8 | Slight distortion, environmental portraits | Street, documentary, context |
| Standard | 50mm | f/1.2-1.8 | Natural perspective, classic look | Portraits, lifestyle, product |
| Short tele | 85mm | f/1.4 | Flattering compression, creamy bokeh | Headshots, beauty, fashion |
| Medium tele | 135mm | f/2 | Strong compression, smooth separation | Editorial portraits, sports |
| Telephoto | 200-400mm | f/2.8 | Extreme compression, subject isolation | Wildlife, sports, paparazzi |
| Macro | 100mm | f/2.8 | Extreme close-up, 1:1 magnification | Product detail, food, texture |
| Tilt-shift | 24-90mm | variable | Selective focus plane, miniature effect | Architecture, creative |

## Composition Templates

- **Rule of thirds**: Subject at intersection points, horizon on upper/lower third
- **Center frame**: Subject dead center, symmetrical elements, Wes Anderson style
- **Leading lines**: Converging lines draw eye to subject, roads, architecture, fences
- **Frame within frame**: Doorways, windows, arches framing the subject
- **Dutch angle**: Tilted camera 15-30 degrees, tension and unease
- **Overhead flat lay**: Camera directly above, 90-degree top-down
- **Eye level**: Camera at subject's eye height, natural and relatable
- **Worm's eye**: Camera at ground level looking up, power and dominance

---

## Batch Processing (Spreadsheet Mode)

When the user uploads a spreadsheet (CSV, XLSX, TSV) with social media posts:

1. Read the file and identify the column containing image descriptions
   (look for columns named: description, image, visual, prompt, image_description, creative, or ask)
2. For each row, also pull context from columns like: platform, date, topic, caption, CTA, audience
3. Use the platform to set aspect ratio:
   - Instagram Feed: 1:1 or 4:5
   - Instagram Story / Reels: 9:16
   - LinkedIn: 1.91:1 (use 16:9)
   - Twitter/X: 16:9
   - Facebook: 16:9
4. Generate the structured JSON prompt for each row
5. Save all prompts to `output/prompts/` as `{date}_{platform}_{slug}.json`
6. Call the API for each prompt
7. Save images to `output/images/` as `{date}_{platform}_{slug}.png`
8. Generate a manifest CSV at `output/manifest.csv` linking rows to their prompt + image files

### Batch Script

Run `scripts/batch_generate.py` for automated processing:

```bash
python scripts/batch_generate.py \
  --input social_calendar.csv \
  --output-dir ./output \
  --api gemini \
  --resolution 2K \
  --rate-limit 10
```

Read `scripts/batch_generate.py` for full implementation details.

---

## Style Presets

When the user asks for a particular vibe, apply these preset overlays on top of the
base prompt structure:

### Corporate / B2B
```
Clean composition, softbox lighting, neutral color palette with brand accent colors,
shallow depth of field, modern office or conference environment, professional wardrobe,
shot on 85mm f/1.4, warm white balance 5500K
```

### Law Enforcement / Government
```
Authoritative framing, structured composition, controlled lighting with cool undertones,
sharp focus throughout (f/8), documentary photography style, muted color grading with
slight teal/blue shift, institutional or operational environment, no dramatic filters
```

### Editorial / Magazine
```
High contrast, dramatic lighting, strong color palette, fashion-forward composition,
shot on medium format, Phase One aesthetic, retouched skin, intentional negative space
for text overlay, magazine-ready crop
```

### Product Hero Shot
```
Clean white or gradient background, three-point studio lighting with key/fill/rim,
product floating or on invisible surface, macro-level detail, reflection on surface,
shot on 100mm macro f/5.6, focus stacked, commercial product photography
```

### Social Media Lifestyle
```
Natural golden hour lighting, candid but styled composition, warm color grading,
slightly desaturated, organic texture, environmental context, relatable human moment,
shot on 35mm f/1.8, shallow depth of field, authentic feel
```

### Cinematic / Dramatic
```
Anamorphic lens flare, 2.39:1 widescreen crop, volumetric lighting, atmospheric haze,
teal and orange color grading, dramatic shadows, high contrast, Alexa 65 film look,
cinematic grain, motivated lighting from practical sources
```

---

## Negative Prompt Library

Always include a negative prompt. Select from these categories and combine:

**Universal negatives** (include with every prompt):
```
watermark, text overlay, logo, signature, low resolution, blurry, noisy,
overexposed, underexposed, artificial, stock photo, clipart
```

**Anti-AI artifacts:**
```
extra fingers, deformed hands, fused limbs, anatomical errors, uncanny valley,
plastic skin, dead eyes, asymmetric face, floating objects
```

**Anti-amateur:**
```
snapshot, selfie, dutch angle (unless intentional), lens distortion,
chromatic aberration, motion blur (unless intentional), harsh on-camera flash,
flat lighting, cluttered background
```

**Anti-overprocessing:**
```
oversaturated, HDR overdone, over-sharpened, posterized, banding,
heavy vignette, excessive lens flare
```

---

## Output File Organization

```
output/
  prompts/
    2026-03-24_instagram_detective-alley.json
    2026-03-24_linkedin_product-launch.json
  images/
    2026-03-24_instagram_detective-alley.png
    2026-03-24_linkedin_product-launch.png
  manifest.csv
```

The manifest CSV should contain these columns:
`row_number, date, platform, description, prompt_file, image_file, aspect_ratio, resolution, status`

---

## Important Notes

- Nano Banana 2 model string: `gemini-3.1-flash-image-preview`
- Nano Banana 2 on fal.ai model ID: `fal-ai/nano-banana-2`
- Set `thinking_level: "high"` on fal.ai for complex prompts (better adherence)
- For the Gemini API, the entire prompt is a single text string in `contents[0].parts[0].text`
- Always save both the structured JSON and the assembled prompt string
- Rate limit: respect API rate limits. Default to 10 requests/minute for batch jobs
- All images include SynthID watermarks (standard for all Nano Banana outputs)
- Supported aspect ratios: auto, 21:9, 16:9, 3:2, 4:3, 5:4, 1:1, 4:5, 3:4, 2:3, 9:16, 4:1, 1:4, 8:1, 1:8
- Supported resolutions (fal.ai): 0.5K, 1K, 2K, 4K
