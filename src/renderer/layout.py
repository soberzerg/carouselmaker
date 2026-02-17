from __future__ import annotations

from PIL import ImageFont


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line: list[str] = []

    for word in words:
        # Truncate single words that exceed max_width
        bbox = font.getbbox(word)
        word_width = bbox[2] - bbox[0]
        if word_width > max_width and not current_line:
            # Truncate with ellipsis
            truncated = word
            while truncated:
                test = truncated + "..."
                tw = font.getbbox(test)[2] - font.getbbox(test)[0]
                if tw <= max_width:
                    lines.append(test)
                    break
                truncated = truncated[:-1]
            else:
                lines.append(word[:3] + "...")
            continue

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
