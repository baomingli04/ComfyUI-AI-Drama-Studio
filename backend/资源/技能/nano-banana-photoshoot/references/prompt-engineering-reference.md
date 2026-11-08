# Prompt Engineering Reference: Photographic Styles

This reference helps Claude Code build richer, more specific assembled prompts by
mapping common request types to detailed photographic direction.

## Subject-Type Prompt Templates

### People / Portraits

**Executive Headshot:**
```
Professional headshot of [subject], shot on 85mm f/1.4 lens, Rembrandt lighting
with softbox key light at 45 degrees, subtle fill card on shadow side, clean
neutral gray background with slight gradient, shallow depth of field, subject
sharp from ear to ear, natural skin texture, warm but not orange skin tones,
catch light in both eyes, confident but approachable expression, business
professional wardrobe, shot at eye level, rule of thirds with eyes on upper
third line
```

**Lifestyle / Candid:**
```
Candid lifestyle moment of [subject] doing [action], shot on 35mm f/1.8,
golden hour natural light, backlit with lens flare, warm color grading with
lifted shadows, authentic and unposed feeling, environmental context visible,
shallow depth of field, subject in natural motion, documentary photography
style, organic composition
```

**Team / Group:**
```
Group of [number] professionals in [setting], shot on 24-70mm f/2.8 at 35mm,
broad even lighting from large overhead softbox, f/5.6 for group depth of field,
all faces equally lit, arranged in dynamic but natural grouping, interaction
between subjects, corporate but not stiff, modern workspace environment
```

### Products

**Hero Product Shot:**
```
[Product] centered on reflective surface, three-point studio lighting: key light
from upper right at 45 degrees, fill light from left, rim light from behind for
edge separation, clean white seamless background, shot on 100mm macro f/8 for
front-to-back sharpness, focus stacked, subtle reflection below product, product
fills 60% of frame, commercial product photography
```

**Product in Context:**
```
[Product] being used in [environment], 50mm f/2.0 lens, product sharp with
environmental bokeh, natural window light supplemented with bounce card,
lifestyle context that shows product benefit, warm and inviting color palette,
product at intersection of rule-of-thirds grid, aspirational but achievable
setting
```

**Flat Lay:**
```
Top-down overhead view of [items] arranged on [surface], shot on 35mm lens at
90-degree overhead angle, even diffused lighting from above, no harsh shadows,
carefully styled with intentional spacing, color-coordinated props, clean
minimalist arrangement, f/5.6 for consistent sharpness across the plane
```

### Architecture / Spaces

**Interior:**
```
Interior photograph of [space], shot on 24mm tilt-shift lens, vertical lines
perfectly straight, natural window light blended with interior ambient, HDR
bracketed for dynamic range, wide composition showing full spatial context,
warm and inviting color temperature, f/8 for deep focus, architectural
photography style
```

**Exterior:**
```
Exterior of [building/space] at [time of day], shot on 17mm ultra-wide,
converging lines corrected, dramatic sky with cloud detail, foreground element
for depth, golden hour or blue hour light, HDR for sky and shadow detail,
architectural magazine quality
```

### Food

**Fine Dining:**
```
[Dish] plated on [plate style] at upscale restaurant, shot on 90mm macro f/2.8,
45-degree angle, single directional window light from left side, dark and moody
background, selective focus on hero element, garnish detail visible, condensation
or steam if hot, muted color palette with food colors popping, food photography
for Michelin-starred establishment
```

**Casual / Social Media:**
```
[Food item] in casual setting, overhead or 30-degree angle, bright and airy
natural light, clean white or marble surface, styled with complementary props
(napkin, utensils, ingredients), vibrant and saturated colors, shot on 50mm f/2.0,
Instagram-ready composition with negative space for text
```

### Technology / Digital

**Device Screenshot Context:**
```
[Device] displaying [screen content], floating at slight angle on clean gradient
background, soft studio lighting with no reflections on screen, device shadow
beneath, screen perfectly sharp and legible, subtle depth of field on background,
commercial technology product photography
```

**Abstract Tech Concept:**
```
Abstract visualization of [concept], clean geometric forms, dark background with
selective illumination, teal and blue color palette with accent highlights,
volumetric light rays, particles or data streams, futuristic but grounded
aesthetic, cinematic wide shot, anamorphic lens quality
```

---

## Color Grading Presets (Detailed)

### Warm Corporate
- Shadows: +5 warm (slightly lifted, never crushed)
- Midtones: Neutral with +3 warmth
- Highlights: Clean white, slight golden cast
- Overall: Natural, inviting, trustworthy
- Reference: Apple, Salesforce brand photography

### Cool Technical
- Shadows: Deep, slightly blue
- Midtones: Neutral to slightly cool
- Highlights: Clean, white, no color cast
- Overall: Precise, modern, authoritative
- Reference: Microsoft, Intel, IBM brand photography

### High Contrast Editorial
- Shadows: Crushed to near-black
- Midtones: Rich, saturated
- Highlights: Blown slightly for drama
- Overall: Bold, attention-grabbing, magazine-cover energy
- Reference: Vogue, GQ, editorial fashion

### Muted / Desaturated
- Shadows: Lifted (fade-to-gray film look)
- Midtones: Desaturated 20-30%
- Highlights: Soft, not blown
- Overall: Contemplative, artsy, premium brand feel
- Reference: Kinfolk, Cereal magazine aesthetic

### Cinematic Teal-Orange
- Shadows: Teal-shifted
- Midtones: Skin tones pushed warm/orange
- Highlights: Warm amber
- Overall: Movie-poster energy, dramatic
- Reference: Michael Bay, David Fincher color grades

---

## Time-of-Day Lighting Map

| Time | Light Quality | Color Temp | Shadows | Best For |
|---|---|---|---|---|
| Pre-dawn (blue hour) | Soft, cool, even | 8000-10000K | Long, subtle | Moody landscapes, contemplative portraits |
| Sunrise (golden hour) | Warm, directional, soft | 3000-4000K | Long, warm | Lifestyle, outdoor portraits, warmth |
| Mid-morning | Bright, slightly warm | 5000-5500K | Defined, medium | Product shots, architecture, food |
| High noon | Harsh, overhead | 5500-6000K | Short, harsh | Avoid for portraits. Good for graphic shadows |
| Late afternoon | Warm, lower angle | 4000-5000K | Lengthening, warm | Everything outdoor, best all-around |
| Sunset (golden hour) | Rich warm, highly directional | 2500-3500K | Very long, dramatic | Hero shots, emotion, drama |
| Twilight (blue hour) | Cool, ambient, even | 7000-9000K | Faint, diffused | Cityscapes, architecture, moody |
| Night | Artificial, mixed | Varies | Multiple from sources | Neon, street, cinematic, noir |

---

## Prompt Length Guidance

Nano Banana 2 responds well to detailed prompts. Target 50-120 words for the assembled
prompt. The model's "thinking" capability means it reasons through complex instructions.

**Too short** (will produce generic results):
> "A photo of a coffee cup"

**Good length** (specific, directed):
> "A steaming ceramic coffee cup on a weathered wooden table in a sunlit cafe,
> morning light streaming through large windows creating warm pools of light and
> soft shadows, shot on 50mm f/1.8 at eye level, shallow depth of field with
> background cafe patrons in soft bokeh, warm color grading with lifted shadows,
> steam visible in the backlight, cozy and inviting mood, professional food and
> lifestyle photography"

**Too long** (model may lose track of early instructions):
> Keep under 200 words. If you need more specificity, prioritize subject and
> lighting details, as those have the highest impact on output quality.
