<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  ${font_faces}
  :root {
    --bg-color: ${bg_color};
    --text-color: ${text_color};
    --accent-color: ${accent_color};
    --heading-font-size: ${heading_font_size}px;
    --body-font-size: ${body_font_size}px;
    --subtitle-font-size: ${subtitle_font_size}px;
    --heading-font: '${heading_font}', sans-serif;
    --body-font: '${body_font}', sans-serif;
    --padding: ${padding}px;
    --line-spacing: ${line_spacing};
    --heading-body-gap: ${heading_body_gap}px;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: 1080px;
    height: 1350px;
    overflow: hidden;
    background: var(--bg-color);
    font-family: var(--body-font);
    color: var(--text-color);
  }
  .slide {
    width: 1080px;
    height: 1350px;
    padding: var(--padding);
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
  }
  .heading {
    font-family: var(--heading-font);
    font-size: var(--heading-font-size);
    line-height: var(--line-spacing);
    color: var(--accent-color);
    text-align: ${heading_alignment};
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  .subtitle {
    font-family: var(--body-font);
    font-size: var(--subtitle-font-size);
    line-height: var(--line-spacing);
    color: var(--text-color);
    text-align: ${heading_alignment};
    margin-top: calc(var(--heading-body-gap) / 2);
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  .body-text {
    font-family: var(--body-font);
    font-size: var(--body-font-size);
    line-height: var(--line-spacing);
    color: var(--text-color);
    margin-top: var(--heading-body-gap);
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  .slide-number {
    position: absolute;
    top: var(--padding);
    right: var(--padding);
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--accent-color);
    color: var(--bg-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--heading-font);
    font-size: 28px;
    font-weight: bold;
  }
  .content-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
</style>
</head>
<body>
${self.body()}
</body>
</html>
