# New Content Templates: Quote, Stats, Steps

**Date:** 2026-02-28
**Status:** Approved
**Scope:** 3 new content templates for expert/coach audience

## Context

Current content templates: text, listing, comparison, hook_overlay.
Target audience: experts, coaches, personal brand builders on LinkedIn/Instagram.

## New Templates

### 1. Quote

Inspirational quote with author attribution.

**Layout:**
```
┌──────────────────────────┐
│     ❝                    │  decorative quotation marks (accent_color)
│   "Quote text here,      │  heading_font_size
│    2-3 lines max"        │
│          — Author Name   │  accent_color, body_font_size
│            Author Title  │  text_color, muted
│                    [N]   │
└──────────────────────────┘
```

**Data model:**
```python
class QuoteData(BaseModel):
    quote_text: str
    author_name: str
    author_title: str = ""
```

### 2. Stats / Big Number

Single prominent metric with context.

**Layout:**
```
┌──────────────────────────┐
│   Context heading        │  body_font_size, text_color
│        340%              │  ~120px, accent_color
│   metric label           │  body_font_size, text_color
│   Additional context     │  smaller, muted
│                    [N]   │
└──────────────────────────┘
```

**Data model:**
```python
class StatsData(BaseModel):
    value: str       # "340%", "$2.5M", "10K+"
    label: str       # "growth in 3 months"
    context: str = ""
```

### 3. Steps

Numbered process with title + description per step.

**Layout:**
```
┌──────────────────────────┐
│   Slide heading          │  heading_font_size
│   ① Step title           │  number in accent circle
│      Step description    │  body_font_size
│   ② Step title           │
│      Step description    │
│   ③ Step title           │
│      Step description    │
│                    [N]   │
└──────────────────────────┘
```

**Data model:**
```python
class StepItem(BaseModel):
    title: str
    description: str = ""

class StepsData(BaseModel):
    items: list[StepItem]  # 2-5 steps
```

## Changes Required

### New files
- `src/renderer/templates/quote.html.mako`
- `src/renderer/templates/stats.html.mako`
- `src/renderer/templates/steps.html.mako`

### Modified files
- `src/schemas/slide.py` — add QuoteData, StatsData, StepItem, StepsData models; extend ContentTemplate enum; add optional fields to SlideContent
- `src/renderer/html_builder.py` — add build_quote_html, build_stats_html, build_steps_html functions
- `src/renderer/engine.py` — route new content_template values to builder functions
- `src/ai/prompts.py` — teach AI about new templates

### Unchanged
- Color style JSONs (templates work with any style)
- DB models (content_template stored as string)
- Celery tasks (work with any slide type)

## Difference from existing templates

| Template | vs Listing | vs Comparison |
|----------|-----------|---------------|
| Quote | Single prominent text block with attribution, not a list | Not a two-sided comparison |
| Stats | Single big number, not multiple items | Not comparing two things |
| Steps | Numbered with title+description per item, visually distinct circles | Sequential process, not opposing sides |
