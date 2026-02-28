<%inherit file="base.html.mako"/>

<div class="slide">
  % if slide_number is not None:
  <div class="slide-number">${"%02d" % slide_number}</div>
  % endif
  <div class="content-wrapper">
    <div class="heading">${heading}</div>
    % if subtitle:
    <div class="subtitle">${subtitle}</div>
    % endif
    % if body_text:
    <div class="body-text">${body_text}</div>
    % endif
  </div>
</div>
