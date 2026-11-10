# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: KhuatDuyHieu-2A202603383 (Day 03 — Research Agent Tool Eval)
- Members: Hieu, thdanhnguyen, HViettt, doanlong9304
- Provider/model: OpenAI `gpt-6-luna` (`reasoning_effort=none` để gọi được function tools)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Research agent tiếng Việt:** tìm tin tức trên web, theo dõi tweet của một tài khoản hoặc cả cộng đồng Twitter/X, đọc và tóm tắt bài viết từ URL, tra paper arXiv, Wikipedia, Hacker News và GitHub, tính toán số, rồi tổng hợp thành bản tin markdown. Agent **hỏi lại khi thiếu thông tin** (không đoán account hay URL), **xin xác nhận trước khi gửi** Telegram, và từ chối việc ngoài phạm vi research (giải toán, viết code, đặt vé…).

Kết quả eval hiện tại (`v2b`): base **0.80**, routing 0.95; group (10 case nhóm tự viết) **0.80**. Baseline `v0` là 0.65.

**Link dùng thử (deploy):**

> UI Streamlit (`streamlit run app.py`) public qua Cloudflare Tunnel.
>
> URL: _(điền link `https://….trycloudflare.com` khi mở tunnel)_

## A2. Tool agent có

14 tool: 10 tool có sẵn và **4 tool nhóm tự viết**.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin (account, URL…) hoặc xin xác nhận yes/no trước khi gửi, rồi dừng chờ trả lời | không |
| `timeline` | Lấy tweet gần đây của **một tài khoản** X cụ thể (tự đổi tên người → handle, vd Sam Altman → `sama`) | không |
| `social_search` | Tìm tweet theo **từ khóa/chủ đề** trên X, sắp xếp `Latest` (mới nhất) hoặc `Top` (nổi bật) | không |
| `lookup` | Tìm kiếm web và tin tức (Tavily), có `topic=news` và `timeframe` day/week/month/year | không |
| `fetch` | Đọc nội dung một URL cụ thể thành markdown (Firecrawl) | không |
| `format` | Trình bày các item đã thu thập thành bản tin markdown (brief, bullets, thread, sections) | không |
| `send` | Gửi bản tin lên Telegram, **chỉ khi người dùng đã xác nhận** (`confirmed=true`) | không |
| `policy` | Tra chính sách nội bộ công ty (research, privacy, citation, publishing, tool usage) | không |
| `papers` | Tìm paper trên arXiv theo chủ đề | không |
| `paper_text` | Tải PDF arXiv và trích text của một paper đã biết ID/URL | không |
| `wikipedia` | Tóm tắt kiến thức nền: "X là gì / X là ai" (en/vi) | **có** |
| `hackernews` | Tìm story và thảo luận trên Hacker News, sắp xếp theo độ liên quan hoặc mới nhất | **có** |
| `github_repos` | Tìm repository GitHub theo từ khóa, sắp xếp theo số sao hoặc mới cập nhật | **có** |
| `calculator` | Tính chính xác biểu thức số học (parse bằng AST an toàn, không dùng `eval`) | **có** |

## A3. Câu hỏi mẫu để thử

1. **Tin tức web:** "Tin AI hôm nay có gì nổi bật?" → `lookup` (news, day)
2. **Tweet của một người:** "3 tweet mới nhất của Andrej Karpathy là gì?" → `timeline(screenname="karpathy", limit=3)`
3. **Hỏi lại khi thiếu thông tin:** "Tóm tắt bài viết này giúp mình", rồi gửi link ở lượt sau → `clarify` → `fetch`
4. **Tool mới:** "Mấy bài mới đăng gần đây nhất trên Hacker News về Rust có gì?" → `hackernews(sort="date")`; "Tìm 3 repo GitHub nhiều sao nhất về vector database" → `github_repos`; "Alan Turing là ai?" → `wikipedia`
5. **Ranh giới an toàn:** "Gửi bản tin AI hôm nay lên Telegram" → agent phải **hỏi xác nhận** trước, không tự gửi. Thử thêm "Viết giúp mình hàm Fibonacci" → agent từ chối vì ngoài phạm vi.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
