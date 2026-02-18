from __future__ import annotations

from pathlib import Path

from mako.lookup import TemplateLookup

_TEMPLATE_DIR = str(Path(__file__).resolve().parent / "templates")

_lookup = TemplateLookup(
    directories=[_TEMPLATE_DIR],
    strict_undefined=True,
    input_encoding="utf-8",
    default_filters=["str", "h"],
)


def render_prompt(template_name: str, **kwargs: object) -> str:
    """Render a Mako template by name and return the stripped result."""
    tmpl = _lookup.get_template(template_name)
    return tmpl.render(**kwargs).strip()  # type: ignore[no-any-return]
