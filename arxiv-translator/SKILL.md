---
name: arxiv-translator
description: >
  Download an arXiv paper's LaTeX source by its ID, translate ALL English text content to Traditional Chinese (繁體中文),
  and compile the translated source into a PDF using xelatex. Use this skill whenever the user mentions translating an
  arXiv paper, converting a paper to Chinese, downloading and translating LaTeX source from arXiv, or gives an arXiv ID
  and asks for a Chinese/Traditional Chinese version. Also trigger when the user says things like "把這篇論文翻譯成中文",
  "幫我翻譯 arXiv 論文", "translate paper 2401.12345", or any combination of arXiv + translate/翻譯. Even if the user
  just provides an arXiv ID and mentions translation or Chinese, use this skill.
---

# arXiv Paper Translator (English → 繁體中文)

This skill downloads an arXiv paper's LaTeX source, translates it to Traditional Chinese, and compiles a translated PDF.

## High-Level Workflow

1. **Download & Extract** — Fetch source from arXiv, detect format, extract
2. **Analyze Structure** — Find all .tex files, identify the main file, understand `\input`/`\include` dependencies
3. **Translate** — Translate each .tex file according to the translation rules below
4. **Post-Translation Review** — Check for missed sections or files
5. **Configure CJK Support** — Inject xelatex + CJK font packages into the preamble
6. **Compile** — Run xelatex (with bibtex/biber if needed) and fix errors if any
7. **Deliver** — Return the compiled PDF to the user

---

## Step 1: Download & Extract

Run the helper script to download and extract the source:

```bash
python3 /path/to/skill/scripts/download_source.py <arxiv_id> <working_dir>
```

The script handles:
- Downloading from `https://arxiv.org/e-print/<arxiv_id>`
- Detecting whether the response is a tar/gz archive or a single .tex file
- Extracting to `<working_dir>/<arxiv_id>/`
- Reporting the list of extracted files

If the script is not available, do it manually:

```bash
ARXIV_ID="2401.12345"  # replace with actual ID
WORK_DIR="/home/claude/arxiv-work"
mkdir -p "$WORK_DIR/$ARXIV_ID"
cd "$WORK_DIR/$ARXIV_ID"

# Download source
curl -L -o source_archive "https://arxiv.org/e-print/$ARXIV_ID"

# Detect format and extract
FILE_TYPE=$(file source_archive)
if echo "$FILE_TYPE" | grep -qi "gzip\|tar"; then
    tar xzf source_archive 2>/dev/null || gunzip -c source_archive > main.tex
elif echo "$FILE_TYPE" | grep -qi "tex\|ascii\|utf-8\|text"; then
    mv source_archive main.tex
fi
rm -f source_archive
```

After extraction, list all files to understand the structure:
```bash
find . -type f | head -50
```

---

## Step 2: Analyze Structure

Before translating, understand the project structure:

1. **Find all .tex files**: `find . -name "*.tex"`
2. **Identify the main file**: Look for the file containing `\documentclass`. This is your entry point.
3. **Map dependencies**: Check for `\input{...}`, `\include{...}`, `\bibliography{...}` to understand which files are included where.
4. **Check for .bib files**: Note if bibtex/biber is needed.
5. **Check for custom .sty or .cls files**: These generally should NOT be translated, but note them.

Important: Do NOT translate:
- `.sty`, `.cls`, `.bst` files (style/class files)
- `.bib` files (bibliography databases)
- Image files
- Any non-tex source files

---

## Step 3: Translate Each .tex File

Create the output directory:
```bash
mkdir -p paper_zh-tw
```

For each .tex file, read the content, translate it, and save to `paper_zh-tw/` preserving the relative path structure. Also copy ALL non-tex files (images, .bib, .sty, .cls, .bst, etc.) to `paper_zh-tw/` so the project remains compilable.

### Translation Rules

These rules are critical — follow them precisely:

#### TRANSLATE (English → 繁體中文):
- **Running text / prose**: All paragraph text, section titles, figure/table captions, footnotes, abstract, acknowledgments
- **Section/chapter headings**: `\section{Introduction}` → `\section{引言}`
- **Captions**: `\caption{Overview of the model}` → `\caption{模型概覽}`
- **Comments in algorithms/code**: Only translate descriptive comments (lines starting with `%` or `//` inside algorithm blocks). Keep variable names and code logic untouched.
- **Theorem/lemma/definition names and content**: Translate the textual content inside theorem environments

#### DO NOT TRANSLATE:
- **Mathematical formulas**: Everything inside `$...$`, `$$...$$`, `\[...\]`, `\(...\)`, and math environments (`equation`, `align`, `gather`, `multline`, etc.) — leave completely untouched
- **LaTeX commands and their structure**: `\begin`, `\end`, `\label`, `\ref`, `\cite`, etc.
- **Person names**: Keep all author names, cited researcher names in English (e.g., "Vaswani et al." stays as is)
- **Code blocks**: Inside `lstlisting`, `verbatim`, `minted` environments — keep code as is, only translate comments
- **Algorithm pseudocode keywords**: `if`, `then`, `else`, `for`, `while`, `return` — keep in English. Only translate descriptive comments.
- **Bibliography content**: `.bib` files and `\bibitem` entries stay in English
- **URLs, DOIs, file paths**
- **Variable names, function names in code**
- **Custom LaTeX commands/macros defined in preamble**: Do not modify `\newcommand`, `\def`, etc.
- **Package names in `\usepackage{}`**

#### TECHNICAL TERMS HANDLING:
Keep all professional and technical terms in English — do NOT translate them to Chinese:
- "attention mechanism" → 保持 "attention mechanism" 不翻譯
- "transformer", "encoder", "decoder", "embedding", "fine-tuning", "gradient descent" etc. → 保持英文原文
- Abbreviations like CNN, RNN, GPU, API, LLM, MoE, KV cache etc. → 保持英文
- Domain-specific terminology (e.g., "throughput", "latency", "inference", "prefill", "token") → 保持英文

#### TRANSLATION STYLE:
- Use formal academic Traditional Chinese (台灣學術用語)
- Use 「」for quotation marks (Traditional Chinese convention)
- Maintain the same paragraph structure
- Keep `~`, `\,`, spacing commands as they are
- If a sentence mixes English names with translatable text, translate only the non-name parts

### Translation Process Per File

For each `.tex` file:

1. Read the entire file content using `view`
2. Translate following the rules above — work section by section for long files
3. Write the translated content to `paper_zh-tw/<same_relative_path>`
4. After writing, briefly verify the output makes sense

When translating, think of the LaTeX source as having two layers:
- **Structural layer** (LaTeX commands) — preserve exactly
- **Content layer** (human-readable text) — translate according to rules

Work carefully. A missed `}` or corrupted command will break compilation.

---

## Step 4: Post-Translation Review

After translating all files, do a thorough review:

1. **File completeness check**:
   ```bash
   # Compare file lists
   echo "=== Original .tex files ==="
   find . -name "*.tex" -not -path "./paper_zh-tw/*" | sort
   echo "=== Translated .tex files ==="
   find paper_zh-tw -name "*.tex" | sort
   ```

2. **Non-tex file copy check**: Make sure all images, .bib, .sty, .cls, .bst files are copied:
   ```bash
   # Copy all non-tex resources to paper_zh-tw if not already done
   rsync -av --exclude="*.tex" --exclude="paper_zh-tw" --exclude="source_archive" ./ paper_zh-tw/
   ```

3. **Content spot-check**: Open 2-3 translated files and verify:
   - No untranslated English paragraphs remain (section content, abstract, etc.)
   - Math formulas are intact
   - LaTeX structure is preserved
   - Person names are kept in English

4. **Section-level audit**: Check the main .tex file's `\section` / `\chapter` commands are all translated. Grep for common untranslated patterns:
   ```bash
   # Look for potentially untranslated section headings
   grep -n "\\\\section{[A-Z]" paper_zh-tw/*.tex
   grep -n "\\\\subsection{[A-Z]" paper_zh-tw/*.tex
   ```

If you find missed content, go back and translate it before proceeding.

---

## Step 5: Configure CJK Support

The translated .tex files need CJK font support to compile with xelatex. Modify the **main .tex file** in `paper_zh-tw/`:

### Add to preamble (after `\documentclass` but before `\begin{document}`):

```latex
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont{Noto Sans CJK TC}
\setCJKsansfont{Noto Sans CJK TC}
\setCJKmonofont{Noto Sans Mono CJK TC}

\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}
```

### Hyperlink support (hyperref):

arXiv's compilation servers **automatically inject `hyperref`** into papers at build time, which is why the original arXiv PDF has clickable cross-references (`\ref`, `\cite`, `\url`). The `.tex` source itself often does NOT explicitly load `hyperref`. Always add it manually to the translated preamble so the output PDF has the same navigation links.

- Place `\usepackage{hyperref}` **after** `fontspec` and `xeCJK` to avoid conflicts.
- Use `colorlinks=true` to style links the same way as the arXiv version (blue, no boxes).
- If the original source already loads `hyperref` explicitly, do not duplicate it — verify that the existing options are compatible with xelatex (no `pdftex` driver option).

### Important considerations:

- If the file already uses `fontspec` or `xeCJK`, don't duplicate — just ensure the CJK font lines are present
- If the document uses `\usepackage[T1]{fontenc}` or `\usepackage[utf8]{inputenc}`, **remove or comment these out** — they conflict with xelatex + fontspec
- If the document uses `pdflatex`-specific packages, you may need to adapt. Common fixes:
  - Remove `\usepackage[pdftex]{graphicx}` → replace with `\usepackage{graphicx}`
  - Remove explicit `pdftex` driver options from other packages

### Install the font if needed:

```bash
# Check if Noto Sans CJK TC is available
fc-list | grep -i "Noto Sans CJK TC"

# If not found, install it
sudo apt-get update && sudo apt-get install -y fonts-noto-cjk
fc-cache -fv
```

---

## Step 6: Compile with xelatex

```bash
cd paper_zh-tw

# First pass
xelatex -interaction=nonstopmode -halt-on-error main.tex

# If there are citations, run bibtex/biber
if grep -q "\\\\bibliography\|\\\\addbibresource" main.tex; then
    # Check if using biblatex (biber) or traditional bibtex
    if grep -q "\\\\usepackage.*biblatex" main.tex; then
        biber main
    else
        bibtex main
    fi
    xelatex -interaction=nonstopmode main.tex
fi

# Final pass for cross-references
xelatex -interaction=nonstopmode main.tex
```

Replace `main.tex` with the actual main file name identified in Step 2.

### Auto-fix common compilation errors:

If compilation fails, examine the `.log` file and try these fixes:

| Error | Fix |
|-------|-----|
| `Font ... not found` | Install missing font or switch to an available one: `fc-list :lang=zh` |
| `Missing $ inserted` | A formula delimiter was likely corrupted during translation — find and fix it |
| `Undefined control sequence` | A LaTeX command was accidentally modified — restore it |
| `inputenc/fontenc conflict` | Remove `inputenc` and `fontenc` packages (xelatex doesn't need them) |
| `Option clash for package` | Remove duplicate package imports or conflicting options |
| Missing packages | `tlmgr install <package>` or `apt-get install texlive-...` |
| `pdftex` driver errors | Remove explicit `pdftex` options from package imports |

After each fix, re-run the compilation. Try up to 3 rounds of auto-fix. If it still fails after 3 attempts, report the remaining errors to the user.

---

## Step 7: Deliver the Result

Once compilation succeeds:

1. Note the path to the generated PDF: `paper_zh-tw/main.pdf` (or whatever the main file name is)
2. Provide a brief summary: paper title (translated), number of pages, any issues encountered

---

## Edge Cases & Tips

- **Very large papers** (>30 pages): Work through files methodically. Don't try to translate an entire large file in one pass — break it into sections.
- **Multi-file projects**: Respect the directory structure. If the original has `sections/intro.tex`, create `paper_zh-tw/sections/intro.tex`.
- **Papers using unusual templates** (e.g., LNCS, IEEE, ACM): These often have strict .cls files. Don't modify the .cls — just add CJK support in the main .tex preamble.
- **Already-translated content**: If parts of the paper are already in Chinese, leave them as is.
- **Encoding**: Ensure all output files are saved as UTF-8.
- **arXiv ID formats**: Support both old format (`0704.0001`) and new format (`2401.12345`). Also handle IDs with version numbers like `2401.12345v2`.
