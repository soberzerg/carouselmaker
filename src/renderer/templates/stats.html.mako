<%inherit file="base.html.mako"/>

<%block name="extra_styles">
<style>
  .stats-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    gap: 16px;
  }
  .stats-heading {
    font-family: var(--body-font);
    font-size: var(--body-font-size);
    color: var(--text-color);
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 2px;
  }
  .stats-value {
    font-family: var(--heading-font);
    font-size: 120px;
    font-weight: 900;
    color: var(--accent-color);
    line-height: 1.1;
    word-break: break-all;
  }
  .stats-label {
    font-family: var(--body-font);
    font-size: calc(var(--body-font-size) * 1.2);
    color: var(--text-color);
    line-height: var(--line-spacing);
  }
  .stats-context {
    font-family: var(--body-font);
    font-size: calc(var(--body-font-size) * 0.85);
    color: var(--text-color);
    opacity: 0.5;
    margin-top: 8px;
    line-height: var(--line-spacing);
  }
</style>
</%block>

<div class="slide">
  % if slide_number is not None:
  <div class="slide-number">${"%02d" % slide_number}</div>
  % endif
  <div class="stats-wrapper">
    <div class="stats-heading">${heading}</div>
    <div class="stats-value">${stats_value}</div>
    <div class="stats-label">${stats_label}</div>
    % if stats_context:
    <div class="stats-context">${stats_context}</div>
    % endif
  </div>
</div>
