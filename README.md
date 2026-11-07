# JunLin｜AI 個人網站（1123junlin.com）

- `content/pages`、`content/posts`：網站內容（Markdown），`content/images`：原始圖片
- `build.py`：產生網站，執行 `python3 build.py`（需要 `pip install markdown pillow`）
- `docs/`：產生出來的網站，GitHub Pages 發佈這個資料夾
- `assets/style.css`：網站樣式

新增文章：在 `content/posts` 新增一個 `.md`（照現有檔案開頭的格式寫標題、日期、分類），執行 `build.py` 後推上 GitHub。
