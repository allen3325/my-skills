# my-skills

收錄一些自己設定的 GitHub Copilot / Claude 自訂 Skills。

---

## Skills 列表

### 1. arxiv-translator

**功用：** 自動下載 arXiv 論文的 LaTeX 原始碼，將所有英文內容翻譯為**繁體中文**（台灣學術用語），並使用 `xelatex` 編譯出翻譯後的 PDF。

**適用情境：**
- 提供 arXiv ID，要求翻譯成中文
- 說出「幫我翻譯 arXiv 論文」、「把這篇論文翻譯成中文」、「translate paper 2401.12345」等指令

**使用方式：**

直接在對話中給出 arXiv ID 並提及翻譯，例如：

```
幫我翻譯 arXiv 論文 2401.12345
```

Skill 會自動執行以下流程：

1. **下載並解壓** — 從 arXiv 取得 LaTeX 原始碼
2. **分析結構** — 找出所有 `.tex` 檔案與相依關係
3. **翻譯** — 依照翻譯規則將英文內容翻譯為繁體中文（保留數學公式、人名、程式碼等不翻譯）
4. **審查** — 檢查是否有遺漏的段落或檔案
5. **設定 CJK 支援** — 注入 `xelatex` + CJK 字型設定
6. **編譯** — 使用 `xelatex` 產生 PDF（含 bibtex/biber 處理）
7. **交付** — 回傳翻譯後的 PDF

**輸出位置：** 翻譯後的檔案會放在原始碼目錄下的 `paper_zh-tw/` 資料夾中。
