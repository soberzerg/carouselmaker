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
    <ol style="
      margin-top: var(--heading-body-gap);
      list-style: none;
      padding: 0;
    ">
      % for item in listing_items:
      <li style="
        display: flex;
        gap: 12px;
        margin-bottom: 10px;
        font-size: var(--body-font-size);
        line-height: var(--line-spacing);
      ">
        <span style="
          color: var(--accent-color);
          font-family: var(--heading-font);
          font-weight: bold;
          min-width: 2em;
          flex-shrink: 0;
        ">${loop.index + 1}.</span>
        <span>${item}</span>
      </li>
      % endfor
    </ol>
  </div>
</div>
