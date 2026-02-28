# New Content Templates (Quote, Stats, Steps) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 3 new content templates (Quote, Stats, Steps) for expert/coach carousel content.

**Architecture:** Extend existing template pattern — add Pydantic data models, Mako HTML templates, builder functions in html_builder, routing in engine, and AI prompt instructions. Each template follows the same pattern as listing/comparison: enum value + data model + Mako file + builder function + engine routing.

**Tech Stack:** Pydantic, Mako templates, HTML/CSS, pytest

**Design doc:** `docs/plans/2026-02-28-new-content-templates-design.md`

---

### Task 1: Add Pydantic data models and extend ContentTemplate enum

**Files:**
- Modify: `src/schemas/slide.py`

**Step 1: Write the failing test**

Add to `tests/test_renderer/test_html_builder.py`:

```python
# At the top, add imports (alongside existing ones):
from src.schemas.slide import (
    QuoteData,
    StatsData,
    StepItem,
    StepsData,
)

class TestQuoteDataModel:
    def test_quote_data_creation(self) -> None:
        q = QuoteData(quote_text="Stay hungry", author_name="Steve Jobs", author_title="Apple CEO")
        assert q.quote_text == "Stay hungry"
        assert q.author_name == "Steve Jobs"
        assert q.author_title == "Apple CEO"

    def test_quote_data_optional_title(self) -> None:
        q = QuoteData(quote_text="Test", author_name="Author")
        assert q.author_title == ""


class TestStatsDataModel:
    def test_stats_data_creation(self) -> None:
        s = StatsData(value="340%", label="growth in 3 months", context="Year over year")
        assert s.value == "340%"
        assert s.label == "growth in 3 months"
        assert s.context == "Year over year"

    def test_stats_data_optional_context(self) -> None:
        s = StatsData(value="10K+", label="users")
        assert s.context == ""


class TestStepsDataModel:
    def test_steps_data_creation(self) -> None:
        items = [
            StepItem(title="Step 1", description="Do this"),
            StepItem(title="Step 2", description="Then this"),
        ]
        sd = StepsData(items=items)
        assert len(sd.items) == 2
        assert sd.items[0].title == "Step 1"

    def test_step_item_optional_description(self) -> None:
        item = StepItem(title="Just a title")
        assert item.description == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer/test_html_builder.py::TestQuoteDataModel -v`
Expected: FAIL with `ImportError: cannot import name 'QuoteData'`

**Step 3: Implement data models**

In `src/schemas/slide.py`, add these models BEFORE the `SlideContent` class (after `ListingData`):

```python
class QuoteData(BaseModel):
    quote_text: str
    author_name: str
    author_title: str = ""


class StatsData(BaseModel):
    value: str
    label: str
    context: str = ""


class StepItem(BaseModel):
    title: str
    description: str = ""


class StepsData(BaseModel):
    items: list[StepItem]
```

Extend the `ContentTemplate` enum with 3 new values:

```python
class ContentTemplate(StrEnum):
    TEXT = "text"
    LISTING = "listing"
    COMPARISON = "comparison"
    QUOTE = "quote"
    STATS = "stats"
    STEPS = "steps"
```

Add optional fields to `SlideContent` (after `comparison_data`):

```python
    quote_data: QuoteData | None = None
    stats_data: StatsData | None = None
    steps_data: StepsData | None = None
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_renderer/test_html_builder.py::TestQuoteDataModel tests/test_renderer/test_html_builder.py::TestStatsDataModel tests/test_renderer/test_html_builder.py::TestStepsDataModel -v`
Expected: all 6 tests PASS

**Step 5: Run all existing tests to check no regressions**

Run: `pytest tests/test_renderer/ -v`
Expected: all existing tests still PASS

**Step 6: Commit**

```bash
git add src/schemas/slide.py tests/test_renderer/test_html_builder.py
git commit -m "feat: add Quote, Stats, Steps data models and ContentTemplate enum values"
```

---

### Task 2: Create Quote Mako template and builder function

**Files:**
- Create: `src/renderer/templates/quote.html.mako`
- Modify: `src/renderer/html_builder.py`
- Modify: `tests/test_renderer/test_html_builder.py`

**Step 1: Write the failing test**

Add to `tests/test_renderer/test_html_builder.py`:

```python
from src.renderer.html_builder import (
    build_comparison_html,
    build_listing_html,
    build_quote_html,
    build_text_html,
)

class TestBuildQuoteHtml:
    def test_contains_quote_text(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Wisdom",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Stay hungry, stay foolish",
                author_name="Steve Jobs",
                author_title="Apple CEO",
            ),
        )
        html = build_quote_html(slide, _make_style())
        assert "Stay hungry, stay foolish" in html
        assert "Steve Jobs" in html
        assert "Apple CEO" in html

    def test_works_without_author_title(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Quote",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Just do it",
                author_name="Nike",
            ),
        )
        html = build_quote_html(slide, _make_style())
        assert "Just do it" in html
        assert "Nike" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Quote",
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Test quote",
                author_name="Author",
            ),
            slide_number=2,
        )
        html = build_quote_html(slide, _make_style())
        assert "02" in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildQuoteHtml -v`
Expected: FAIL with `ImportError: cannot import name 'build_quote_html'`

**Step 3: Create the Mako template**

Create `src/renderer/templates/quote.html.mako`:

```mako
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
```

**Step 4: Add builder function**

In `src/renderer/html_builder.py`, add after `build_comparison_html`:

```python
def build_quote_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render quote template HTML."""
    assert slide.quote_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "quote_text": slide.quote_data.quote_text,
        "author_name": slide.quote_data.author_name,
        "author_title": slide.quote_data.author_title,
    })
    tmpl = _lookup.get_template("quote.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildQuoteHtml -v`
Expected: all 3 tests PASS

**Step 6: Commit**

```bash
git add src/renderer/templates/quote.html.mako src/renderer/html_builder.py tests/test_renderer/test_html_builder.py
git commit -m "feat: add Quote template (Mako + builder function + tests)"
```

---

### Task 3: Create Stats Mako template and builder function

**Files:**
- Create: `src/renderer/templates/stats.html.mako`
- Modify: `src/renderer/html_builder.py`
- Modify: `tests/test_renderer/test_html_builder.py`

**Step 1: Write the failing test**

Add to `tests/test_renderer/test_html_builder.py`:

```python
from src.renderer.html_builder import (
    build_comparison_html,
    build_listing_html,
    build_quote_html,
    build_stats_html,
    build_text_html,
)

class TestBuildStatsHtml:
    def test_contains_value_and_label(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Our Growth",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(
                value="340%",
                label="growth in 3 months",
                context="Year over year comparison",
            ),
        )
        html = build_stats_html(slide, _make_style())
        assert "340%" in html
        assert "growth in 3 months" in html
        assert "Year over year comparison" in html
        assert "Our Growth" in html

    def test_works_without_context(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Metric",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(value="$2.5M", label="revenue"),
        )
        html = build_stats_html(slide, _make_style())
        assert "$2.5M" in html
        assert "revenue" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Stats",
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(value="10K+", label="users"),
            slide_number=4,
        )
        html = build_stats_html(slide, _make_style())
        assert "04" in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildStatsHtml -v`
Expected: FAIL with `ImportError: cannot import name 'build_stats_html'`

**Step 3: Create the Mako template**

Create `src/renderer/templates/stats.html.mako`:

```mako
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
```

**Step 4: Add builder function**

In `src/renderer/html_builder.py`, add after `build_quote_html`:

```python
def build_stats_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render stats/big-number template HTML."""
    assert slide.stats_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "heading": slide.heading,
        "stats_value": slide.stats_data.value,
        "stats_label": slide.stats_data.label,
        "stats_context": slide.stats_data.context,
    })
    tmpl = _lookup.get_template("stats.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildStatsHtml -v`
Expected: all 3 tests PASS

**Step 6: Commit**

```bash
git add src/renderer/templates/stats.html.mako src/renderer/html_builder.py tests/test_renderer/test_html_builder.py
git commit -m "feat: add Stats template (Mako + builder function + tests)"
```

---

### Task 4: Create Steps Mako template and builder function

**Files:**
- Create: `src/renderer/templates/steps.html.mako`
- Modify: `src/renderer/html_builder.py`
- Modify: `tests/test_renderer/test_html_builder.py`

**Step 1: Write the failing test**

Add to `tests/test_renderer/test_html_builder.py`:

```python
from src.renderer.html_builder import (
    build_comparison_html,
    build_listing_html,
    build_quote_html,
    build_stats_html,
    build_steps_html,
    build_text_html,
)

class TestBuildStepsHtml:
    def test_contains_steps(self) -> None:
        slide = SlideContent(
            position=1,
            heading="How to Start",
            content_template=ContentTemplate.STEPS,
            steps_data=StepsData(items=[
                StepItem(title="Define your goal", description="Be specific about what you want"),
                StepItem(title="Make a plan", description="Break it down into small tasks"),
                StepItem(title="Take action", description="Start with the first task today"),
            ]),
        )
        html = build_steps_html(slide, _make_style())
        assert "How to Start" in html
        assert "Define your goal" in html
        assert "Be specific about what you want" in html
        assert "Make a plan" in html
        assert "Take action" in html

    def test_works_without_step_descriptions(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Quick Steps",
            content_template=ContentTemplate.STEPS,
            steps_data=StepsData(items=[
                StepItem(title="First step"),
                StepItem(title="Second step"),
            ]),
        )
        html = build_steps_html(slide, _make_style())
        assert "First step" in html
        assert "Second step" in html

    def test_slide_number_rendered(self) -> None:
        slide = SlideContent(
            position=1,
            heading="Steps",
            content_template=ContentTemplate.STEPS,
            steps_data=StepsData(items=[
                StepItem(title="Only step"),
            ]),
            slide_number=5,
        )
        html = build_steps_html(slide, _make_style())
        assert "05" in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildStepsHtml -v`
Expected: FAIL with `ImportError: cannot import name 'build_steps_html'`

**Step 3: Create the Mako template**

Create `src/renderer/templates/steps.html.mako`:

```mako
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
```

**Step 4: Add builder function**

In `src/renderer/html_builder.py`, add after `build_stats_html`:

```python
def build_steps_html(slide: SlideContent, style: StyleConfig) -> str:
    """Render steps template HTML."""
    assert slide.steps_data is not None
    ctx = _base_context(style)
    ctx.update({
        "slide_number": slide.slide_number,
        "heading": slide.heading,
        "steps_items": slide.steps_data.items,
    })
    tmpl = _lookup.get_template("steps.html.mako")
    return tmpl.render(**ctx)  # type: ignore[no-any-return]
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_renderer/test_html_builder.py::TestBuildStepsHtml -v`
Expected: all 3 tests PASS

**Step 6: Commit**

```bash
git add src/renderer/templates/steps.html.mako src/renderer/html_builder.py tests/test_renderer/test_html_builder.py
git commit -m "feat: add Steps template (Mako + builder function + tests)"
```

---

### Task 5: Wire new templates into the rendering engine

**Files:**
- Modify: `src/renderer/engine.py`
- Modify: `tests/test_renderer/test_engine.py`

**Step 1: Write the failing tests**

Add to `tests/test_renderer/test_engine.py` (import new models at top alongside existing imports):

```python
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    QuoteData,
    SlideContent,
    SlideType,
    StatsData,
    StepItem,
    StepsData,
    TextPosition,
)
```

Add new test class:

```python
class TestNewContentTemplates:
    async def test_quote_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=2,
            heading="Wisdom",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.QUOTE,
            quote_data=QuoteData(
                quote_text="Stay hungry, stay foolish",
                author_name="Steve Jobs",
                author_title="Apple CEO",
            ),
            slide_number=2,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_stats_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=3,
            heading="Our Impact",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.STATS,
            stats_data=StatsData(value="340%", label="growth"),
            slide_number=3,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_steps_template_renders(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=4,
            heading="How to Start",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.STEPS,
            steps_data=StepsData(items=[
                StepItem(title="Plan", description="Define goals"),
                StepItem(title="Execute"),
            ]),
            slide_number=4,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)

    async def test_quote_without_data_falls_back_to_text(self) -> None:
        renderer = SlideRenderer(_make_style())
        slide = SlideContent(
            position=2,
            heading="Fallback Quote",
            body_text="Some text",
            slide_type=SlideType.CONTENT,
            content_template=ContentTemplate.QUOTE,
            quote_data=None,
            slide_number=2,
        )
        result = await renderer.render(slide=slide)
        assert _png_dimensions(result) == (SLIDE_WIDTH, SLIDE_HEIGHT)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_renderer/test_engine.py::TestNewContentTemplates -v`
Expected: FAIL — quote/stats/steps templates are not routed yet in engine

**Step 3: Update engine routing**

In `src/renderer/engine.py`, update imports:

```python
from src.renderer.html_builder import (
    build_comparison_html,
    build_hook_overlay_html,
    build_listing_html,
    build_quote_html,
    build_stats_html,
    build_steps_html,
    build_text_html,
)
```

Update `_render_content_template` method to add new template routing:

```python
    async def _render_content_template(self, slide: SlideContent) -> bytes:
        """Dispatch to the appropriate HTML template."""
        if slide.content_template == ContentTemplate.LISTING and slide.listing_data:
            html = build_listing_html(slide, self.style)
        elif (
            slide.content_template == ContentTemplate.COMPARISON
            and slide.comparison_data
        ):
            html = build_comparison_html(slide, self.style)
        elif slide.content_template == ContentTemplate.QUOTE and slide.quote_data:
            html = build_quote_html(slide, self.style)
        elif slide.content_template == ContentTemplate.STATS and slide.stats_data:
            html = build_stats_html(slide, self.style)
        elif slide.content_template == ContentTemplate.STEPS and slide.steps_data:
            html = build_steps_html(slide, self.style)
        else:
            html = build_text_html(slide, self.style)
        return await render_html_to_png(html, self.width, self.height)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_renderer/test_engine.py::TestNewContentTemplates -v`
Expected: all 4 tests PASS

**Step 5: Run all renderer tests to check no regressions**

Run: `pytest tests/test_renderer/ -v`
Expected: all tests PASS

**Step 6: Commit**

```bash
git add src/renderer/engine.py tests/test_renderer/test_engine.py
git commit -m "feat: wire Quote, Stats, Steps templates into rendering engine"
```

---

### Task 6: Update AI prompt to teach Claude about new templates

**Files:**
- Modify: `src/ai/templates/copywriter_system.mako`

**Step 1: Update the system prompt**

In `src/ai/templates/copywriter_system.mako`, after the existing comparison template instructions (after line 38), add:

```
If content_template is "quote":
  - Add "quote_data": {"quote_text": "The actual quote text", "author_name": "Author Name", "author_title": "Optional title/role"}
  - heading and subtitle of the slide itself are NOT used in quote layout.
  - body_text should be empty.
  - Use for: inspirational quotes, expert wisdom, client testimonials, memorable phrases.
  - author_title is optional (can be "").

If content_template is "stats":
  - Add "stats_data": {"value": "340%", "label": "growth in 3 months", "context": "Year over year comparison"}
  - heading is used as a context label above the big number.
  - body_text should be empty. subtitle is NOT used.
  - value is a string — can include symbols like "$2.5M", "10K+", "3x".
  - context is optional (can be "").
  - Use for: key metrics, impressive numbers, data highlights.

If content_template is "steps":
  - Add "steps_data": {"items": [{"title": "Step title", "description": "Optional description"}, ...]}
  - heading is used as the slide title above the steps.
  - 2-5 steps recommended. Each step has a title (max 5 words) and optional description (max 15 words).
  - body_text should be empty. subtitle is NOT used.
  - Use for: how-to guides, processes, numbered sequences, action plans.
```

Update the output section (currently line 47-50) to include new template fields:

```
Output MUST be valid JSON array of objects with keys: "position", "heading", "subtitle", "body_text", "text_position", "slide_type", "image_description".
For "content" slides, also include "content_template".
For "listing" templates, also include "listing_items".
For "comparison" templates, also include "comparison_data".
For "quote" templates, also include "quote_data".
For "stats" templates, also include "stats_data".
For "steps" templates, also include "steps_data".
Do not include any text outside the JSON array.
```

Update the content template enum description (currently line 18-19):

```
- Each CONTENT slide MUST have a "content_template" field — one of "text", "listing", "comparison", "quote", "stats", "steps".
```

Update the template choice section (lines 20-23):

```
- Choose the template that best fits the content of each slide:
  - "text" — for narrative paragraphs, explanations, single ideas. Uses heading + subtitle + body_text.
  - "listing" — for enumerations, features, tips. Requires "listing_items" field.
  - "comparison" — for contrasting two options, before/after, pros/cons. Requires "comparison_data" field.
  - "quote" — for inspirational quotes, expert wisdom, testimonials. Requires "quote_data" field.
  - "stats" — for key metrics, impressive numbers, data highlights. Requires "stats_data" field.
  - "steps" — for how-to guides, processes, action plans. Requires "steps_data" field.
```

**Step 2: Run existing tests to verify no regressions**

Run: `pytest tests/ -v`
Expected: all tests PASS

**Step 3: Commit**

```bash
git add src/ai/templates/copywriter_system.mako
git commit -m "feat: update AI prompt with Quote, Stats, Steps template instructions"
```

---

### Task 7: Update AI response parser to handle new template data

**Files:**
- Modify: `src/ai/anthropic_provider.py`
- Modify: `tests/test_ai/test_template_loader.py` (or add new test file)

**Step 1: Write the failing test**

Create or add to tests for the parser. Add to a test file (e.g., `tests/test_ai/test_parse_slide.py`):

```python
from __future__ import annotations

from src.ai.anthropic_provider import _parse_slide
from src.schemas.slide import ContentTemplate


class TestParseSlideNewTemplates:
    def test_parse_quote_slide(self) -> None:
        raw = {
            "position": 2,
            "heading": "Wisdom",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "quote",
            "quote_data": {
                "quote_text": "Stay hungry",
                "author_name": "Steve Jobs",
                "author_title": "Apple CEO",
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.QUOTE
        assert slide.quote_data is not None
        assert slide.quote_data.quote_text == "Stay hungry"
        assert slide.quote_data.author_name == "Steve Jobs"

    def test_parse_stats_slide(self) -> None:
        raw = {
            "position": 3,
            "heading": "Growth",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "stats",
            "stats_data": {
                "value": "340%",
                "label": "growth",
                "context": "",
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.STATS
        assert slide.stats_data is not None
        assert slide.stats_data.value == "340%"

    def test_parse_steps_slide(self) -> None:
        raw = {
            "position": 4,
            "heading": "How to Start",
            "subtitle": "",
            "body_text": "",
            "text_position": "none",
            "slide_type": "content",
            "image_description": "",
            "content_template": "steps",
            "steps_data": {
                "items": [
                    {"title": "Plan", "description": "Make a plan"},
                    {"title": "Execute", "description": ""},
                ],
            },
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.STEPS
        assert slide.steps_data is not None
        assert len(slide.steps_data.items) == 2

    def test_quote_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 2,
            "heading": "Bad Quote",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "quote",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT
        assert slide.quote_data is None

    def test_stats_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 3,
            "heading": "Bad Stats",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "stats",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT

    def test_steps_without_data_falls_back_to_text(self) -> None:
        raw = {
            "position": 4,
            "heading": "Bad Steps",
            "subtitle": "",
            "body_text": "fallback",
            "text_position": "center",
            "slide_type": "content",
            "image_description": "",
            "content_template": "steps",
        }
        slide = _parse_slide(raw)
        assert slide.content_template == ContentTemplate.TEXT
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai/test_parse_slide.py -v`
Expected: FAIL — `_parse_slide` doesn't handle new template data yet

**Step 3: Update the parser**

In `src/ai/anthropic_provider.py`, update the imports:

```python
from src.schemas.slide import (
    ComparisonBlock,
    ComparisonData,
    ContentTemplate,
    ListingData,
    QuoteData,
    SlideContent,
    SlideType,
    StatsData,
    StepItem,
    StepsData,
    TextPosition,
)
```

Update `_parse_slide` function. After the line that pops `comparison_raw` (line 34), add:

```python
    quote_raw = raw.pop("quote_data", None)
    stats_raw = raw.pop("stats_data", None)
    steps_raw = raw.pop("steps_data", None)
```

After the comparison parsing block (after line 58), add:

```python
    # Transform quote dict into QuoteData
    if isinstance(quote_raw, dict) and slide.content_template == ContentTemplate.QUOTE:
        try:
            slide.quote_data = QuoteData(**quote_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid quote_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.quote_data = None

    # Transform stats dict into StatsData
    if isinstance(stats_raw, dict) and slide.content_template == ContentTemplate.STATS:
        try:
            slide.stats_data = StatsData(**stats_raw)
        except (TypeError, ValueError):
            logger.warning("Invalid stats_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.stats_data = None

    # Transform steps dict into StepsData
    if isinstance(steps_raw, dict) and slide.content_template == ContentTemplate.STEPS:
        try:
            items = [StepItem(**item) for item in steps_raw.get("items", [])]
            slide.steps_data = StepsData(items=items)
        except (TypeError, ValueError, KeyError):
            logger.warning("Invalid steps_data for slide %d, falling back to text", slide.position)
            slide.content_template = ContentTemplate.TEXT
            slide.steps_data = None
```

After the existing fallback checks (lines 61-66), add:

```python
    # If quote template but no data, fall back to text
    if slide.content_template == ContentTemplate.QUOTE and not slide.quote_data:
        slide.content_template = ContentTemplate.TEXT

    # If stats template but no data, fall back to text
    if slide.content_template == ContentTemplate.STATS and not slide.stats_data:
        slide.content_template = ContentTemplate.TEXT

    # If steps template but no data, fall back to text
    if slide.content_template == ContentTemplate.STEPS and not slide.steps_data:
        slide.content_template = ContentTemplate.TEXT
```

Also update the `generate_slides` method: in the loop that enforces non-content slides use text template (around line 126-129), add clearing of new data fields:

```python
        # Enforce: non-content slides always use text template
        for s in slides:
            if s.slide_type != SlideType.CONTENT:
                s.content_template = ContentTemplate.TEXT
                s.listing_data = None
                s.comparison_data = None
                s.quote_data = None
                s.stats_data = None
                s.steps_data = None
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_ai/test_parse_slide.py -v`
Expected: all 6 tests PASS

**Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: all tests PASS

**Step 6: Commit**

```bash
git add src/ai/anthropic_provider.py tests/test_ai/test_parse_slide.py
git commit -m "feat: update AI response parser for Quote, Stats, Steps templates"
```

---

### Task 8: Final integration verification

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: ALL tests PASS

**Step 2: Run linting**

Run: `make lint`
Expected: no errors

**Step 3: Run formatting**

Run: `make format`
Expected: no changes needed (or auto-fixed)

**Step 4: Final commit if formatting changed anything**

```bash
git add -A
git commit -m "style: formatting fixes"
```
