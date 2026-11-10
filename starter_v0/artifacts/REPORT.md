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

## A1. Agent này làm được gì

**Research agent tiếng Việt:** tìm tin tức trên web, theo dõi tweet của một tài khoản hoặc cả cộng đồng Twitter/X, đọc và tóm tắt bài viết từ URL, tra paper arXiv, Wikipedia, Hacker News và GitHub, tính toán số, rồi tổng hợp thành bản tin markdown. Agent **hỏi lại khi thiếu thông tin** (không đoán account hay URL), **xin xác nhận trước khi gửi** Telegram, và từ chối việc ngoài phạm vi research (giải toán, viết code, đặt vé…).

Kết quả eval hiện tại (`v2b`): base **0.80**, routing 0.95; group (10 case nhóm tự viết) **0.80**. Baseline `v0` là 0.65.

**Link dùng thử (deploy):**

> UI Streamlit (`streamlit run app.py`) public qua Cloudflare Tunnel.
>
> URL: https://postcards-regard-ethical-pitch.trycloudflare.com/

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
| v0 | baseline | n/a (baseline starter prompt/tools on openai gpt-6-luna) | n/a | case_acc=0.65 routing=0.80 args=0.65 multiturn=0.83 | runs/v0_B_base_openai_20261110T095815539037.json |
| v1 | system_prompt.md | Removing guess/send-without-confirm instructions and requiring clarify fixes missing_info + wrong_boundary | case_acc=0.65 | case_acc=0.55 routing=0.85 args=0.55 multiturn=0.50 | runs/v1_B_base_openai_20261110T101417806341.json |
| v1b | system_prompt.md | The "never invent handles" sentence stops the model mapping a named person to their handle | case_acc=0.55 | case_acc=0.70 routing=0.90 args=0.70 multiturn=0.83 | runs/v1b_B_base_openai_20261110T101547908400.json |
| v1c | system_prompt.md | Softening 'Always finish in a single step / Pick one tool' stops forced tool calls on out_of_scope queries | case_acc=0.70 | case_acc=0.80 routing=1.00 args=0.80 multiturn=0.83 | runs/v1c_B_base_openai_20261110T101922117035.json |
| v2 | tools.yaml | Explicit WHEN/WHEN NOT boundary descriptions on new tools prevent routing collisions with existing core tools | case_acc=0.80 | case_acc=0.80 routing=1.00 args=0.80 multiturn=0.83 | runs/v2_B_base_openai_20261110T104228751676.json |
| v2b | tools.yaml | Adding 2 more tools with when/when-not descriptions keeps base accuracy at v2 level | case_acc=0.80 | case_acc=0.80 routing=0.95 args=0.80 multiturn=0.83 | runs/v2b_B_base_openai_20261110T105236817463.json |
| v2b-group | data/eval_group.json | Team cases expose out_of_scope action requests and yes_no confirm boundary as remaining weaknesses | n/a | case_acc=0.80 routing=0.90 args=0.80 multiturn=0.80 | runs/v2b_B_group_openai_20261110T105040796999.json |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | missing_info | timeline | Tự đoán handle `@sama` thay vì gọi clarify | Bắt buộc gọi clarify khi thiếu thông tin tài khoản |
| R11_missing_url | missing_info | fetch | Tự đoán URL openai.com thay vì gọi clarify | Bắt buộc gọi clarify khi thiếu URL cụ thể |
| R12_confirm_before_send | wrong_boundary | send | Tự ý gửi với `confirmed=true` chưa hỏi người dùng | Thiết lập boundary an toàn: chỉ gửi khi người dùng đã xác nhận |
| R14_out_of_scope_coding | out_of_scope | format | Ép gọi tool format cho yêu cầu viết code python | Đổi chỉ dẫn single-step sang "Consider finish...", cho phép trả lời trực tiếp |
| R03_web_news_routing | wrong_arg_value | lookup | Truy vấn query quá dài, không trích xuất đúng từ khóa | Định nghĩa rõ quy ước trích xuất query, topic=news, timeframe |
| R13_parallel_web_and_tweets | wrong_tool | lookup | Thiếu lệnh gọi song song `social_search` | Cho phép agent thực hiện multi-tool calls song song |
| M02_carryover_timeframe | wrong_arg_value | lookup | Query mang theo cụm từ thời gian dư thừa | Quy định rõ timeframe đi vào parameter `timeframe`, không để trong `query` |

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
