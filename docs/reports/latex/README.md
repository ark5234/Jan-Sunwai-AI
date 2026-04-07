# Jan-Sunwai AI LaTeX Report

## Structure

- `main.tex` - Main report file
- `frontmatter/` - Abbreviations, definitions, and screenshot list
- `chapters/` - Chapter-wise content (Chapter 1 to Chapter 11)

## Build

From this folder (`docs/reports/latex`):

```bash
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Run twice so table/figure/page references settle.

## Screenshot Assets

Expected screenshot path:

- `docs/images/screenshots/`

The report compiles even if screenshots are missing; placeholder boxes are shown automatically.
