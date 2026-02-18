from __future__ import annotations

COPYWRITER_SYSTEM_PROMPT = """\
You are an expert copywriter specializing in viral LinkedIn and Instagram carousels.

Your task: transform the user's text into a series of carousel slides.

Rules:
- Each slide has:
  - "heading" (max 8 words) — punchy, attention-grabbing title
  - "subtitle" (max 15 words) — supporting line that reinforces the heading (optional, can be "")
  - "body_text" (2-3 sentences) — detailed content (optional, can be "")
  - "text_position" — where body_text should appear: "center", "bottom", or "none" (if no body_text)
  - "slide_type" — one of "hook", "content", "cta"
- The FIRST slide MUST be "hook" type — it grabs attention immediately. Hook slides should have a \
strong heading + subtitle, but NO body_text (set body_text to "" and text_position to "none").
- The LAST slide MUST be "cta" type — a call to action. CTA slides should have a clear heading + \
subtitle with minimal or no body_text.
- Middle slides are "content" type — they carry the main message.
- If a slide has body_text, set text_position to "center" or "bottom".
- If a slide has no body_text, set text_position to "none".
- Keep language concise, impactful, and easy to read on mobile.
- Match the tone to the chosen style preset.

Output MUST be valid JSON array of objects with keys: "position", "heading", "subtitle", \
"body_text", "text_position", "slide_type".
Do not include any text outside the JSON array.
"""

COPYWRITER_USER_PROMPT = """\
Style: {style_slug}
Number of slides: {slide_count}

User text:
<user_text>
{input_text}
</user_text>
"""

# ── Slide image generation prompt ────────────────────────

SLIDE_TYPE_INSTRUCTIONS: dict[str, str] = {
    "hook": (
        "This is the HOOK slide — the first thing viewers see. "
        "Make it visually striking and impossible to scroll past. "
        "Use bold, dramatic composition. The text should be the hero element."
    ),
    "content": (
        "This is a CONTENT slide — the main informational body. "
        "Design should be engaging but let the text be readable. "
        "Use balanced composition with clear visual hierarchy."
    ),
    "cta": (
        "This is the CTA (call-to-action) slide — the final slide. "
        "Design should motivate action. Make it feel conclusive and energizing. "
        "The text should feel like an invitation or command."
    ),
}

CLEAN_ZONE_INSTRUCTIONS: dict[str, str] = {
    "center": (
        "Leave a CLEAN ZONE in the center of the slide (roughly the middle 40% vertically) "
        "where additional text will be overlaid later. This zone should have a subdued or "
        "semi-transparent background so overlaid text remains readable."
    ),
    "bottom": (
        "Leave a CLEAN ZONE in the bottom third of the slide where additional text will be "
        "overlaid later. This zone should have a subdued or semi-transparent background so "
        "overlaid text remains readable."
    ),
    "none": "No clean zone needed — the image with baked-in text is the complete slide.",
}

TEXT_AREA_DESCRIPTIONS: dict[str, str] = {
    "center": "Place the heading and subtitle in the upper portion of the slide.",
    "bottom": "Place the heading and subtitle in the upper half of the slide.",
    "none": "Center the heading and subtitle as the main visual focus of the entire slide.",
}

SLIDE_IMAGE_PROMPT_TEMPLATE = """\
Create a complete, professional carousel slide image for social media (LinkedIn/Instagram).

=== SLIDE CONTENT ===
Heading: {heading}
Subtitle: {subtitle}

=== DESIGN REQUIREMENTS ===
- Resolution: EXACTLY 1080x1350 pixels (portrait orientation)
- The heading and subtitle text MUST be rendered directly into the image with beautiful typography
- Text must be crisp, properly kerned, and perfectly readable
- Use professional layout and composition

=== STYLE ===
Style name: {style_name}
Mood: {style_mood}
Description: {style_description}
Color palette:
  - Background: {bg_color}
  - Text color: {text_color}
  - Accent color: {accent_color}
{visual_hints}

=== TEXT PLACEMENT ===
{text_area_description}

=== SLIDE TYPE ===
{slide_type_instruction}

=== CLEAN ZONE ===
{clean_zone_instruction}

=== RULES ===
- Render the heading in large, bold typography using the accent color ({accent_color})
- Render the subtitle in smaller, lighter typography using the text color ({text_color})
- Background should complement the text, not compete with it
- Do NOT add any text other than the provided heading and subtitle
- The image must look like a professionally designed social media slide
- Ensure high contrast between text and background for readability
"""
