<%inherit file="base.html.mako"/>

<%block name="extra_styles">
<style>
  .comparison-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
  }
  .comp-block {
    flex: 1;
    border-radius: 20px;
    padding: 36px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .before-block {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .before-block .block-title {
    font-family: var(--heading-font);
    font-size: calc(var(--heading-font-size) * 1.05);
    font-weight: 700;
    color: rgba(${accent_r}, ${accent_g}, ${accent_b}, 0.55);
    line-height: 1.2;
  }
  .before-block .block-subtitle {
    font-family: var(--body-font);
    font-size: calc(var(--body-font-size) * 1.2);
    color: rgba(255, 255, 255, 0.4);
    line-height: 1.3;
  }
  .before-block .comp-item {
    font-size: calc(var(--body-font-size) * 0.95);
    color: rgba(255, 255, 255, 0.35);
    line-height: 1.2;
  }
  .after-block {
    background: linear-gradient(
      to bottom,
      rgba(${accent_r}, ${accent_g}, ${accent_b}, 0.85),
      rgba(${accent_r}, ${accent_g}, ${accent_b}, 1)
    );
    border: 1px solid rgba(${accent_r}, ${accent_g}, ${accent_b}, 0.25);
  }
  .after-block .block-title {
    font-family: var(--heading-font);
    font-size: calc(var(--heading-font-size) * 1.05);
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.2;
  }
  .after-block .block-subtitle {
    font-family: var(--body-font);
    font-size: calc(var(--body-font-size) * 1.2);
    color: rgba(255, 255, 255, 0.75);
    line-height: 1.3;
  }
  .after-block .comp-item {
    font-size: calc(var(--body-font-size) * 0.95);
    color: rgba(255, 255, 255, 0.85);
    line-height: 1.2;
  }
  .badge {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: bold;
  }
  .badge-x {
    background: rgba(255, 69, 58, 0.12);
    color: #FF453A;
  }
  .badge-check {
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
  }
  .vs-label {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-family: var(--heading-font);
    font-size: calc(var(--heading-font-size) * 1.2);
    font-weight: 700;
    color: var(--accent-color);
    z-index: 10;
    text-shadow:
      0 0 40px var(--bg-color),
      0 0 20px var(--bg-color),
      0 0 60px var(--bg-color);
  }
  .comp-items {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
  }
</style>
</%block>

<div class="slide">
  <div class="comparison-wrapper">
    <!-- Before block (top, muted) -->
    <div class="comp-block before-block">
      <div class="badge badge-x">&#x2717;</div>
      <div class="block-title">${top_label}</div>
      % if top_subtitle:
      <div class="block-subtitle">${top_subtitle}</div>
      % endif
      <div class="comp-items">
        % for item in top_items:
        <div class="comp-item">&#x2022;&ensp;${item}</div>
        % endfor
      </div>
    </div>

    <!-- VS overlay -->
    <div class="vs-label">VS</div>

    <!-- After block (bottom, vibrant) -->
    <div class="comp-block after-block">
      <div class="badge badge-check">&#x2713;</div>
      <div class="block-title">${bottom_label}</div>
      % if bottom_subtitle:
      <div class="block-subtitle">${bottom_subtitle}</div>
      % endif
      <div class="comp-items">
        % for item in bottom_items:
        <div class="comp-item">&#x2022;&ensp;${item}</div>
        % endfor
      </div>
    </div>
  </div>
</div>
