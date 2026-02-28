<%inherit file="base.html.mako"/>

<%block name="extra_styles">
<style>
  .quote-mark {
    font-size: 120px;
    color: var(--accent-color);
    font-family: Georgia, serif;
    line-height: 0.8;
    opacity: 0.6;
  }
  .quote-text {
    font-family: var(--heading-font);
    font-size: var(--heading-font-size);
    line-height: var(--line-spacing);
    color: var(--text-color);
    font-style: italic;
    margin-top: 20px;
  }
  .quote-author {
    margin-top: var(--heading-body-gap);
    font-family: var(--body-font);
    font-size: var(--body-font-size);
    color: var(--accent-color);
    font-weight: bold;
  }
  .quote-author-title {
    font-family: var(--body-font);
    font-size: calc(var(--body-font-size) * 0.85);
    color: var(--text-color);
    opacity: 0.6;
    margin-top: 8px;
  }
</style>
</%block>

<div class="slide">
  % if slide_number is not None:
  <div class="slide-number">${"%02d" % slide_number}</div>
  % endif
  <div class="content-wrapper">
    <div class="quote-mark">&#x201C;</div>
    <div class="quote-text">${quote_text}</div>
    <div class="quote-author">&#x2014; ${author_name}</div>
    % if author_title:
    <div class="quote-author-title">${author_title}</div>
    % endif
  </div>
</div>
