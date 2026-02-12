# GeoNode Documentation

## How to write Documentation

GeoNode uses MarkDown, with [Python Markdown](https://python-markdown.github.io/) support and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) extensions.

### Setup 
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Develop
```bash
mkdocs serve --livereload 
```

### Build
```bash
export ENABLE_PDF_EXPORT=1
mkdocs build 
```

## Reference documentation

  - [MkDocs](https://www.mkdocs.org/)
  - [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/reference/)
  - [Python Markdown](https://python-markdown.github.io/)

