from __future__ import annotations

from PIL import ImageFont


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        test_line = " ".join([*current_line, word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def calculate_text_height(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    line_spacing: float,
) -> int:
    """Calculate total height of wrapped text block."""
    if not lines:
        return 0

    line_height = font.getbbox("Ag")[3]
    total = int(line_height * len(lines) * line_spacing)
    return total
