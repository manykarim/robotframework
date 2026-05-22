## Context

The `def_list` extension produces loose rendering (with `<p>`-wrapped `<dd>` elements) only when definitions span multiple paragraphs. For single-paragraph definitions separated by blank lines, it produces a flat `<dl>` without `<p>` wrappers. However, the Material theme applies `margin: 1em 0` to `<dt>` elements and `margin: 1em 0 1em 1.875em` to `<dd>` elements, creating ~2em of vertical space between consecutive items.

**Important:** blank lines between def-list items are syntactically required by Python-Markdown's `def_list` extension — removing them causes items to be rendered as deeply nested `<dl>` trees instead of sibling terms. The blank lines must be preserved in the source.

## Goals / Non-Goals

**Goals:**
- Reduce the visual gap between consecutive definition list items so that each term and its definition read as a unit.
- Make the rendered output match the compact layout the user expects.

**Non-Goals:**
- Changing any Markdown source files or the conversion pipeline.
- Removing blank lines from def-list source (breaks the extension's grammar).
- Changing spacing for `<dl>` elements in non-def-list contexts.

## Decisions

**CSS override in `extra.css`**
The spacing comes entirely from Material's base stylesheet applied to `<dt>` and `<dd>`. Adding targeted CSS overrides in the project's existing `stylesheets/extra.css` is the minimal, correct, and upgrade-safe approach. No Markdown source changes needed.

**Override values**
- `dt`: reduce top margin to `0.5em`, bottom margin to `0` — keeps breathing room before each new term while eliminating the gap between term and its definition.
- `dd`: reduce top margin to `0`, bottom margin to `0.75em` — definition sits flush under the term; a small bottom margin separates it from the next term.

## Risks / Trade-offs

- These overrides apply to all `<dl>` elements rendered by the `def_list` extension across the whole site. If any def list intentionally uses loose/spaced rendering, it will also be compacted. Given the guide's usage, this is the desired behaviour everywhere.
