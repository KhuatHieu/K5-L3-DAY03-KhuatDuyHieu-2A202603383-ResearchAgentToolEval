# TASKS — Day 03 Research Agent (team 4 người)

Base đã dựng sẵn (commit `chore: base scaffold`):
- `starter_v0/app.py` — UI Streamlit **chạy được**, dùng chung vòng lặp tool của `chat.py`, ghi `transcripts/*.transcript.json`.
- 4 tool mới đã có khung: `tools/{wikipedia,hackernews,github_repos,calculator}/` (`tool.py` stub + `TOOL.md` + khối yaml mẫu), **đã đăng ký** trong `tools/__init__.py`, **chưa** thêm vào `tools.yaml` (để baseline v0 không đổi).
- Test stub cho từng tool: `tests/test_tool_<name>.py` (mỗi file 3 test `skip`).
- `streamlit` đã thêm vào `requirements.txt`.

## Luật chung (đọc trước khi code)

1. **Ownership file** — chỉ sửa file của mình. Cần sửa file người khác → nhắn owner.
   | File | Owner |
   |---|---|
   | `artifacts/system_prompt.md`, description tool **cũ** trong `artifacts/tools.yaml`, `artifacts/version_log.csv`, `runs/` | Hieu |
   | `tools/wikipedia/`, `tools/hackernews/`, `tests/test_tool_{wikipedia,hackernews}.py` | thdanhnguyen |
   | `tools/github_repos/`, `tools/calculator/`, `tests/test_tool_{github_repos,calculator}.py`, `tests/test_tools_todo.py`, bug fix tool cũ | HViettt |
   | `app.py`, `data/eval_group.json`, `artifacts/REPORT.md`, `artifacts/poster.html` | doanlong9304 |
2. **Branch**: `feat/<tên-việc>` → PR/merge vào `main` sớm và thường xuyên. `git pull --rebase` trước khi push.
3. Thêm tool vào `tools.yaml`: **chỉ append ở CUỐI file**, gửi Hieu review description (vì đổi `tools_hash` → ảnh hưởng eval).
4. Trước khi merge: `pytest` phải **0 failed** (`tests/test_tool_contract.py` luôn xanh).
5. Không đổi tên tool có sẵn. Không sửa nội dung case trong `data/eval_base.json`. Không commit `.env`.

## T0 — Setup (MỖI NGƯỜI, 10 phút, làm ngay)

```bash
git pull
cd starter_v0
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # điền key Hieu gửi qua chat riêng
python scripts/preflight_provider.py --provider openrouter
pytest                    # kỳ vọng: 62 passed, 29 skipped
streamlit run app.py      # mở http://localhost:8501 thử 1 câu
```
DoD: preflight pass, pytest không fail, UI trả lời được 1 câu.

---

## 👤 Hieu — Prompt/Eval lead

**H1. Phân phối key + chạy baseline v0** (ngay)
- Điền `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY` → gửi team qua kênh riêng.
- `python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json`
- `python scripts/parse_runs.py runs/ --output analysis/base_runs.csv`
- DoD: dòng `v0` trong `version_log.csv`; post vào group **bảng case FAIL + loại lỗi** (`wrong_tool`, `wrong_arg_value`, `missing_info`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`) để doanlong9304 dùng cho report & eval case.

**H2. v1 — bỏ chỉ dẫn xấu trong `system_prompt.md`** (deadline 15:30)
- Giả thuyết: prompt ép đoán / tự gửi / một bước gây `missing_info` + `wrong_boundary`.
- Bỏ: đoán thay vì hỏi, chọn bừa Sam Altman, tự đoán URL, gửi không xác nhận, ép một bước.
- DoD: chạy `v1`, ghi metric trước/sau.

**H3. v2 — routing rule + description tool cũ** (deadline 16:00)
- Prompt: khi nào `timeline` / `social_search` / `lookup` / `fetch` / `clarify` / `format`.
- `tools.yaml`: viết lại description từng tool cũ (làm gì, khi nào dùng / KHÔNG dùng).
- Merge các tool mới đã xong của thdanhnguyen/HViettt **trước** khi chạy v2, ghi chú trong `reason`.
- DoD: chạy `v2`, ghi log.

**H4. v3 — convention args + boundary `send`** (deadline 17:30)
- Handle không có `@`, `topic=news` cho tin tức, `timeframe`, `search_type=Top|Latest`, `send` chỉ khi `confirmed=true`.
- Chạy `v3` cả 3 suite: `base`, `group` (`data/eval_group.json`), `extension`.
- DoD: `version_log.csv` có v0–v3, mỗi version **một** giả thuyết.

**H5. Report Phần B — B1 (version evidence), B2 (failure analysis)**.

---

## 👤 thdanhnguyen — Tool dev 1 (`wikipedia`, `hackernews`)

**D1. Implement `tools/wikipedia/tool.py`** → `wikipedia_summary(topic, lang="en")` (deadline 15:30)
- API: `GET https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}` (không key). Fallback opensearch nếu 404.
- Trả `{"tool","topic","lang","title","summary","url"}`; lỗi → `err(...)`, không raise. Dùng `requests.get` (để mock được).
- DoD: 3 test trong `tests/test_tool_wikipedia.py` pass (happy path mock HTTP, input xấu, HTTP lỗi).

**D2. Implement `tools/hackernews/tool.py`** → `hn_search(query, sort="relevance", limit=5)` (deadline 16:00)
- API: `GET https://hn.algolia.com/api/v1/search` (`sort=date` → `/search_by_date`), `params={"query":..,"tags":"story","hitsPerPage":limit}`.
- Item: `title, url, points, num_comments, created_at, hn_url`. Coerce `limit` (chuỗi/0/âm).
- DoD: 3 test pass.

**D3. Đăng ký vào `tools.yaml`** — copy khối yaml trong `TOOL.md`, viết description có "khi nào dùng/không dùng", append cuối file → nhờ Hieu review → `pytest tests/test_tool_contract.py` xanh.

**D4. Gửi doanlong9304** 2–3 câu hỏi mẫu nên route tới tool của mình (cho eval case + Phần A).

**D5 (bonus nếu xong sớm)**: Step 7 — Ollama `qwen2.5:7b` + `llama3.2:3b` chạy base eval với prompt v3.

---

## 👤 HViettt — Tool dev 2 + Test challenge (`github_repos`, `calculator`)

**V1. Implement `tools/calculator/tool.py`** → `calculate(expression)` (deadline 15:30)
- **Không dùng `eval`**: `ast.parse(mode="eval")` + whitelist (`BinOp`, `UnaryOp`, `Constant` số, `+ - * / // % **`). Chặn số mũ quá lớn.
- Trả `{"tool","expression","value"}`; `1/0`, chuỗi rỗng, `__import__` → error dict.
- DoD: 3 test trong `tests/test_tool_calculator.py` pass.

**V2. Implement `tools/github_repos/tool.py`** → `search_github_repos(query, sort="stars", limit=5)` (deadline 16:00)
- API: `GET https://api.github.com/search/repositories`, `params={"q","sort","per_page"}`, header `Accept: application/vnd.github+json`. Nếu có env `GITHUB_TOKEN` thì gửi `Authorization`.
- Item: `name, url, description, stars, language, updated_at`.
- DoD: 3 test pass. Đăng ký `tools.yaml` như D3.

**V3. Test challenge `tests/test_tools_todo.py`** (sau 16:00)
- Điền 17 stub (clarify, format, send, lookup, fetch, timeline, social_search, policy).
- Thử input biên: `limit=0`, `top_k=0`, `max_results="5"`, `items` thiếu `url`. Bug thật → sửa tool, giữ test làm regression, ghi vào REPORT B5 (gửi doanlong9304).
- DoD: `pytest` → **0 failed, 0 skipped** cho toàn bộ repo.

**V4.** Gửi doanlong9304 2–3 câu hỏi mẫu cho tool của mình.

---

## 👤 doanlong9304 — UI + Eval case + Report

**L1. Polish UI `app.py` + deploy** (deadline 16:15)
- Base đã chạy được. Thêm: nút câu hỏi mẫu, hiển thị trạng thái `waiting_for_user` (clarify), nút xác nhận cho `send` nếu muốn, giao diện gọn.
- Cài `cloudflared`, chạy `cloudflared tunnel --url http://localhost:8501`, dán link vào REPORT A1. Giữ tunnel chạy suốt showdown.

**L2. 10 eval case `data/eval_group.json`** (deadline 16:00)
- 5 single-turn (`query`) + 5 multi-turn (`turns`). Mỗi case: `id`, `phase:"B"`, `failure_type`, `expect`, `metadata.what_it_tests`. Copy format từ `data/eval_base.json`.
- Phủ: clarify khi thiếu account/URL, `send` không xác nhận → không gửi, `topic=news`, out_of_scope (`no_tool`), **≥1 case route tới mỗi tool mới** (chỉ thêm case tool mới sau khi tool đó đã có trong `tools.yaml`, nếu không contract test fail).
- DoD: `pytest tests/test_tool_contract.py` xanh; gửi Hieu chạy suite `group`.

**L3. REPORT Phần A + poster** (deadline **16:30 — cứng**)
- A1 mô tả + link, A2 bảng tool (đánh dấu 4 tool mới), A3 3–5 câu hỏi mẫu (lấy từ D4/V4).
- Tùy chọn `artifacts/poster.html`.

**L4. Live chat transcript** — ≥3 lượt qua `python chat.py --provider openrouter --version v3` (hoặc UI): 1 research thường, 1 thiếu info rồi bổ sung, 1 "gửi Telegram" kiểm tra agent hỏi xác nhận.

**L5. Report Phần B** — B3 eval cases, B4 live chat, B5 (từ HViettt), B6 reflection; gom B1/B2 từ Hieu.

---

## Timeline

| Giờ | Hieu | thdanhnguyen | HViettt | doanlong9304 |
|---|---|---|---|---|
| ngay | T0, H1 (key + v0) | T0, D1 | T0, V1 | T0, L1 |
| 15:30 | H2 v1 | D1 merge → D2 | V1 merge → V2 | L2 |
| 16:00 | H3 v2 (đã có tool mới) | D3, D4 | V2 merge, V3 | L2 xong, L3 |
| 16:30 | — **Showdown** — | | | Phần A + link |
| 17:30 | H4 v3, H5 | D5 bonus | V3 xong | L4, L5 |

## Checklist nộp bài
- [ ] `version_log.csv` v0–v3 · [ ] `runs/*.json` · [ ] `transcripts/*.transcript.json`
- [ ] 4 tool mới trong `tools.yaml` + registry + TOOL.md + ≥3 test/tool (bonus: UI + >3 tool)
- [ ] `eval_group.json` 10 case · [ ] `pytest` 0 failed / 0 skipped
- [ ] UI + link · [ ] REPORT A (16:30) + B
