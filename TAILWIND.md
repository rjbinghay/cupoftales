# Tailwind setup — StorySip

This project uses **Tailwind CSS v4** (CSS-first config) with the official
Typography plugin for article body styling.

## File map

```
package.json                         build scripts (npm run dev / build)
static/css/input.css                 source — design tokens, base, components
static/css/main.css                  ← generated, gitignored
stories/templates/stories/base.html  loads {% static 'css/main.css' %}
```

All styling decisions live in **`static/css/input.css`**. There is no
`tailwind.config.js` — v4 reads tokens from the `@theme` block in CSS.

## First-time setup

```bash
npm install
```

## Daily workflow

```bash
# In one terminal:
npm run dev          # rebuilds main.css on every template/CSS save

# In another:
python manage.py runserver
```

## Production build

```bash
npm run build        # minified main.css; commit to deploy or run on CI
```

## Where to put new styles

| You want to…                                  | Edit                                          |
| --------------------------------------------- | --------------------------------------------- |
| Change a color, font, or spacing token        | `@theme` block in `input.css`                 |
| Tweak default heading / body styles           | `@layer base` in `input.css`                  |
| Add a reusable component (card, button, etc.) | `@layer components` in `input.css`            |
| One-off utility on a single element           | Tailwind classes directly in the template     |

Rule of thumb: if a class string repeats in 3+ places, promote it to a
component class in `input.css`.

## The `.prose-story` class

Wrap rendered story body in `<div class="prose-story">…</div>`. The Tailwind
Typography plugin handles paragraph spacing, blockquotes, lists, and links
with reading-optimized defaults (65ch measure, serif body, 1.6 line-height).
