<%inherit file="base.html.mako"/>

<%block name="extra_styles">
<style>
  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 24px;
    margin-top: var(--heading-body-gap);
  }
  .step-item {
    display: flex;
    gap: 20px;
    align-items: flex-start;
  }
  .step-number {
    width: 52px;
    height: 52px;
    min-width: 52px;
    border-radius: 50%;
    background: var(--accent-color);
    color: var(--bg-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--heading-font);
    font-size: 26px;
    font-weight: bold;
  }
  .step-content {
    flex: 1;
  }
  .step-title {
    font-family: var(--heading-font);
    font-size: calc(var(--body-font-size) * 1.15);
    font-weight: bold;
    color: var(--text-color);
    line-height: 1.3;
  }
  .step-description {
    font-family: var(--body-font);
    font-size: var(--body-font-size);
    color: var(--text-color);
    opacity: 0.7;
    line-height: var(--line-spacing);
    margin-top: 6px;
  }
</style>
</%block>

<div class="slide">
  % if slide_number is not None:
  <div class="slide-number">${"%02d" % slide_number}</div>
  % endif
  <div class="content-wrapper">
    <div class="heading">${heading}</div>
    <div class="steps-list">
      % for step in steps_items:
      <div class="step-item">
        <div class="step-number">${loop.index + 1}</div>
        <div class="step-content">
          <div class="step-title">${step.title}</div>
          % if step.description:
          <div class="step-description">${step.description}</div>
          % endif
        </div>
      </div>
      % endfor
    </div>
  </div>
</div>
