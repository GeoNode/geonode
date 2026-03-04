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

## Editing tips

- **Images**:
  - Can be embedded with `![](img/geo_limits_003.png)`, where the path is relative to the .md page
  - Can flow on the side of the text by appending the align attriute, for example  `![](img/geo_limits_003.png) { align=left }`
  - Captions (if needed) can be added with a `\\\ caption \\\` block right below the image. E.g.
    ```
    ![](img/geo_limits_003.png)
    /// caption
    Image caption
    ///
    ```
- **Links**: Beyond the standard Markdown links, we haveAnchors to headings and other pages is available:
  - Anchors can be created by placing this `()[]{ #my-anchor }` anywhere, and can be linked from anywhere with `[My anchor][my-anchor]`
  - Links to other pages can be done by referencing the page name (and optionally the heading) `[project license](about.md#license)`
- **[Admonition blocks](https://squidfunk.github.io/mkdocs-material/reference/admonitions/#usage)** can be created with:
  ```
  !!! Warning
      The warning text
  ```
- **Inline emojis** are supported and their code can be searched with [this tool](https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/#search).
- Support for **[content tabs](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/#content-tabs)** is enabled, in case they're useful.

## Reference documentation

  - [MkDocs](https://www.mkdocs.org/)
  - [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/reference/)
  - [Python Markdown](https://python-markdown.github.io/)

