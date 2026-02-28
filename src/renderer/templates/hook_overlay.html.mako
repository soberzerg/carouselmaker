<%inherit file="base.html.mako"/>

<%block name="extra_styles">
<style>
  .slide-overlay {
    width: 1080px;
    height: 1350px;
    background-image: url('${image_data_uri}');
    background-size: cover;
    background-position: center;
    position: relative;
    display: flex;
    flex-direction: column;
    ${"justify-content: flex-end;" if text_position == "bottom" else "justify-content: center;"}
    padding: var(--padding);
  }
  .overlay-strip {
    background: rgba(${bg_r}, ${bg_g}, ${bg_b}, ${body_text_bg_opacity});
    padding: 30px var(--padding);
    margin: 0 calc(-1 * var(--padding));
    width: calc(100% + 2 * var(--padding));
  }
  .overlay-strip .body-text {
    margin-top: 0;
  }
</style>
</%block>

<div class="slide-overlay">
  <div class="overlay-strip">
    <div class="body-text">${body_text}</div>
  </div>
</div>
