<%def name="slide_type_instruction()">\
% if slide_type == "hook":
This is the HOOK slide — the first thing viewers see. \
Make it visually striking and impossible to scroll past. \
Use bold, dramatic composition. The text should be the hero element.\
% elif slide_type == "cta":
This is the CTA (call-to-action) slide — the final slide. \
Design should motivate action. Make it feel conclusive and energizing. \
The text should feel like an invitation or command.\
% else:
This is a CONTENT slide — the main informational body. \
Design should be engaging but let the text be readable. \
Use balanced composition with clear visual hierarchy.\
% endif
</%def>\
<%def name="clean_zone_instruction()">\
% if text_position == "center":
Leave a CLEAN ZONE in the center of the slide (roughly the middle 40% vertically) \
where additional text will be overlaid later. This zone should have a subdued or \
semi-transparent background so overlaid text remains readable.\
% elif text_position == "bottom":
Leave a CLEAN ZONE in the bottom third of the slide where additional text will be \
overlaid later. This zone should have a subdued or semi-transparent background so \
overlaid text remains readable.\
% else:
No clean zone needed — the image with baked-in text is the complete slide.\
% endif
</%def>\
<%def name="text_area_description()">\
% if text_position == "center":
Place the heading and subtitle in the upper portion of the slide.\
% elif text_position == "bottom":
Place the heading and subtitle in the upper half of the slide.\
% else:
Center the heading and subtitle as the main visual focus of the entire slide.\
% endif
</%def>\
Create a complete, professional carousel slide image for social media (LinkedIn/Instagram).

=== SLIDE CONTENT ===
Heading: ${heading}
Subtitle: ${subtitle}

=== DESIGN REQUIREMENTS ===
- Resolution: EXACTLY 1080x1350 pixels (portrait orientation)
- The heading and subtitle text MUST be rendered directly into the image with beautiful typography
- Text must be crisp, properly kerned, and perfectly readable
- Use professional layout and composition

=== STYLE ===
Style name: ${style_name}
Mood: ${style_mood}
Description: ${style_description}
Color palette:
  - Background: ${bg_color}
  - Text color: ${text_color}
  - Accent color: ${accent_color}
${visual_hints}

=== TEXT PLACEMENT ===
${text_area_description()}

=== SLIDE TYPE ===
${slide_type_instruction()}

=== CLEAN ZONE ===
${clean_zone_instruction()}

=== RULES ===
- Render the heading in large, bold typography using the accent color (${accent_color})
- Render the subtitle in smaller, lighter typography using the text color (${text_color})
- Background should complement the text, not compete with it
- Do NOT add any text other than the provided heading and subtitle
- The image must look like a professionally designed social media slide
- Ensure high contrast between text and background for readability