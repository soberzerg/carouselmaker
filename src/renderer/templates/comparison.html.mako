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
    <div style="
      margin-top: var(--heading-body-gap);
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 0;
    ">
      <!-- Top block -->
      <div style="
        flex: 1;
        border: 2px solid var(--accent-color);
        border-radius: 16px;
        padding: 24px;
        background: rgba(${accent_r}, ${accent_g}, ${accent_b}, 0.12);
      ">
        <div style="
          font-family: var(--heading-font);
          font-size: calc(var(--body-font-size) * 1.2);
          color: var(--accent-color);
          margin-bottom: 8px;
          line-height: 1.3;
        ">${top_label}</div>
        <ul style="list-style: none; padding: 0;">
          % for item in top_items:
          <li style="
            font-size: var(--body-font-size);
            line-height: var(--line-spacing);
          ">&#x2022; ${item}</li>
          % endfor
        </ul>
      </div>

      <!-- VS separator -->
      <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 90px;
        position: relative;
      ">
        <div style="
          position: absolute;
          left: 0; right: 0;
          top: 50%;
          height: 2px;
          background: var(--accent-color);
        "></div>
        <div style="
          width: 70px; height: 70px;
          border-radius: 50%;
          background: var(--accent-color);
          color: var(--bg-color);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: var(--heading-font);
          font-size: 48px;
          font-weight: bold;
          position: relative;
          z-index: 1;
        ">VS</div>
      </div>

      <!-- Bottom block -->
      <div style="
        flex: 1;
        border: 2px solid var(--accent-color);
        border-radius: 16px;
        padding: 24px;
        background: rgba(${accent_r}, ${accent_g}, ${accent_b}, 0.12);
      ">
        <div style="
          font-family: var(--heading-font);
          font-size: calc(var(--body-font-size) * 1.2);
          color: var(--accent-color);
          margin-bottom: 8px;
          line-height: 1.3;
        ">${bottom_label}</div>
        <ul style="list-style: none; padding: 0;">
          % for item in bottom_items:
          <li style="
            font-size: var(--body-font-size);
            line-height: var(--line-spacing);
          ">&#x2022; ${item}</li>
          % endfor
        </ul>
      </div>
    </div>
  </div>
</div>
