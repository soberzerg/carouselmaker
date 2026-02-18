<%def name="slide_type_instruction()">\
% if slide_type == "hook":
This is a HOOK slide — the very first thing viewers see in the carousel. \
Make it visually striking and impossible to scroll past. \
Use bold, dramatic composition with high visual contrast. \
The heading text should be the dominant hero element, large and commanding.\
% elif slide_type == "cta":
This is a CTA (call-to-action) slide — the final slide in the carousel. \
The design should motivate immediate action and feel conclusive and energizing. \
The heading text should feel like a direct invitation or a bold command.\
% else:
This is a CONTENT slide — the main informational body of the carousel. \
The design should be engaging yet let the text remain easily readable. \
Use balanced composition with clear visual hierarchy between heading and subtitle.\
% endif
</%def>\
<%def name="clean_zone_instruction()">\
% if text_position == "center":

=== CLEAN ZONE ===
Reserve the center of the slide (roughly the middle 40% vertically) as a clean zone \
with a subdued background — additional text will be overlaid there later.\
% elif text_position == "bottom":

=== CLEAN ZONE ===
Reserve the bottom third of the slide as a clean zone with a subdued background — additional text will be overlaid there later.\
% endif
</%def>\
<%def name="text_placement_instruction()">\
% if text_position == "center":
Place the heading and subtitle in the upper portion of the slide, above the reserved clean zone.\
% elif text_position == "bottom":
Place the heading and subtitle in the upper half of the slide, above the reserved clean zone.\
% else:
Center the heading and subtitle as the main visual focus of the entire slide.\
% endif
</%def>\
Design a professional social media carousel slide image in portrait orientation, exactly 1080 pixels wide by 1350 pixels tall.

The purpose of this slide is a ${style_name}-styled carousel for LinkedIn and Instagram. \
The overall mood is ${style_mood}. ${style_description}.

=== TEXT TO RENDER ===
Render the following heading text in large, bold typography using the accent color (${accent_color}):
"${heading}"
% if subtitle:

Render the following subtitle text in smaller, lighter typography using the text color (${text_color}):
"${subtitle}"
% endif

Only these exact text strings should appear in the image — no other words, labels, or watermarks.

=== TYPOGRAPHY ===
The heading "${heading}" should be rendered in a bold, clean, sans-serif font with excellent kerning and anti-aliasing. \
Make the text crisp and perfectly legible against the background.
% if subtitle:
The subtitle "${subtitle}" should use a lighter weight of the same font family, \
clearly smaller than the heading to establish visual hierarchy.
% endif

=== TEXT PLACEMENT ===
${text_placement_instruction()}

=== SLIDE TYPE ===
${slide_type_instruction()}

=== VISUAL SCENE ===
% if image_description:
The background visual scene for this slide: ${image_description}
Adapt this scene to fit the slide's color palette and style while keeping the described mood and objects.
% else:
Use an abstract background that matches the style mood.
% endif

=== COMPOSITION & STYLE ===
Color palette: background ${bg_color}, text ${text_color}, accents ${accent_color}.
% if visual_hints:
${visual_hints}
% endif

The background should complement and support the text, never compete with it. \
Ensure strong contrast between the text and the background for maximum readability. \
The final result should look like a professionally designed, publication-ready social media slide.
${clean_zone_instruction()}

=== FORMAT ===
Output a single image at exactly 1080x1350 pixels, portrait orientation.