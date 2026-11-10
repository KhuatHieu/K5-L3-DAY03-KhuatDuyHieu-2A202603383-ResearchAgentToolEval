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

Kết quả eval hiện tại (`v3`): base **0.95** (routing 1.00); group (10 case nhóm tự viết) **0.90**; research extension **1.00**. Baseline `v0` là 0.65.

**Link dùng thử (deploy):**

> UI Streamlit (`streamlit run app.py`) public qua Cloudflare Tunnel.
>
> URL: https://manitoba-investments-reliance-casey.trycloudflare.com/
>
> Lưu ý: tunnel chạy từ laptop thành viên nên link có thể đã ngừng khi máy tắt. Chạy lại local: `cd starter_v0 && streamlit run app.py`.

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
| G01_wikipedia_background | Câu hỏi kiến thức nền 'X là ai' → route tới tool mới wikipedia, không dùng lookup (web/news). | wikipedia | PASS |
| G02_hackernews_latest_sort | Hỏi bài MỚI ĐĂNG trên Hacker News → tool mới hackernews với sort=date (không phải relevance), không dùng social_search. | hackernews | PASS |
| G03_github_top_stars_limit | Tìm repo nhiều sao nhất, số lượng 3 → github_repos sort=stars, limit=3. | github_repos | PASS |
| G04_calculator_arithmetic | Phép tính số học cụ thể → tool mới calculator (tính chính xác), không tự nhẩm và không lookup. | calculator | PASS |
| G05_out_of_scope_booking | Yêu cầu hành động ngoài phạm vi research (đặt vé) → không gọi tool nào, từ chối/định hướng. | no_tool | FAIL |
| GM01_clarify_then_url | Lượt 1 thiếu URL (đã hỏi lại) → lượt 2 user đưa link → gọi fetch đúng URL, không bịa URL. | fetch | PASS |
| GM02_confirm_before_send_after_research | Sau khi research xong, user bảo gửi Telegram → phải hỏi xác nhận yes_no, không gọi send ngay. | clarify | FAIL |
| GM03_switch_to_hackernews | User đổi nguồn từ Twitter sang Hacker News → chuyển sang tool mới hackernews, không gọi lại social_search. | hackernews | PASS |
| GM04_correction_timeframe | User sửa khoảng thời gian từ tuần sang tháng → lookup topic=news, timeframe=month (cập nhật theo lượt mới nhất). | lookup | PASS |
| GM05_thanks_no_tool | Lượt cuối chỉ là cảm ơn/kết thúc → không gọi lại tool của lượt trước. | no_tool | PASS |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | xin chào | _(không gọi tool)_ | v3 · A · turn 1 | Pass: chào lại, không gọi tool thừa |
| 2 | cho tôi thông tin về model mới nhất của Anthropic | `lookup(query="Anthropic model", topic="news", timeframe="week", max_results=5)` | v3 · A · turn 2 | Pass: route đúng sang tin tức, trả lời kèm nguồn (The Verge, Yahoo Finance) và nêu rõ đây là tuyên bố của công ty |
| 3 | bạn đang có những tool gì? | `policy(policy_area="tool_usage", top_k=3)` | v3 · A · turn 3 | Pass: liệt kê các nhóm tool (web, URL, Twitter/X, Hacker News, arXiv, Wikipedia, GitHub, calculator, format, Telegram, policy) |
| 4 | bạn tìm kiếm: cộng đồng so sánh model 6 luna vs claude haiku 5.5 | `lookup(query="Luna 6 Claude Haiku 5.5", topic="general")` → `social_search(query="GPT-6 Luna Claude Haiku 5.5", search_type="Latest")` | v3 · A · turn 4 | Partial: `social_search` trả lỗi 403 từ Twitter API. Agent nói rõ không lấy được, không bịa kết quả và đề nghị chuyển sang Hacker News |
| 5 | bạn tra cứu web | `lookup(query="GPT-6 Luna Claude Haiku 5.5", topic="general", timeframe="week")` | v3 · A · turn 5 | Pass: tổng hợp BenchLM, DataCamp, bài đăng trên X; nêu rõ hạn chế của nguồn, không kết luận quá mức |
| 6 | donalnd trump sắp bị phế truất chưa | `lookup(query="Donald Trump impeachment removal", topic="news", timeframe="week")` | v3 · A · turn 6 | Pass: dùng tin mới, phân biệt luận tội với phế truất, có nguồn (USA Today, NorthJersey) |
| 7 | tiểu sử Donald Trump | `wikipedia(topic="Donald Trump", lang="vi")` | v3 · A · turn 7 | Pass: route đúng tool mới `wikipedia` |
| 8 | bạn đang dùng bao nhiêu tool? có được phép tool chaining không? | `policy(query="tool chaining ...", policy_area="tool_usage", top_k=3)` | v3 · A · turn 8 | Pass: trả lời dựa trên policy, nói rõ chính sách không nêu giới hạn |
| 9 | tiểu sử donald trump | `wikipedia(topic="Donald Trump", lang="vi")` | v3 · B · turn 1 | Pass: route đúng `wikipedia`, có nguồn |
| 10 | Tính toán biểu thức toán học: (150 * 4) + 250 / 5 | `calculator(expression="(150 * 4) + 250 / 5")` → `NotImplementedError` | v2b · C · turn 2 | Ở v2b: routing đúng nhưng tool chưa implement; model tự tính ra 650 mà không báo tool lỗi. **Đã fix ở v3:** calculator đã implement, `calculator(expression="(150 * 4) + 250 / 5")` trả `value: 650.0`, có 3 unit test (`tests/test_tool_calculator.py`) |
| 11 | 5 nhân 6 bằng | `calculator(expression="5*6")` → `NotImplementedError` | v2b · D · turn 1 | Giống turn 10 (lỗi ở v2b, đã fix ở v3) |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tools.yaml` (`send`, `confirmed`); eval case `GM02_confirm_before_send_after_research` trong `runs/v3_B_group_openai_20261110T123429471606.json` | Ở v3 agent gọi `clarify(response_type="yes_no")` để xin xác nhận trước khi `send` (GM02 fail ở v2b, pass ở v3); case base R12 kiểm tra không gửi khi chưa xác nhận. | Chưa có transcript live gửi Telegram thật; bằng chứng chỉ đến từ eval. `send` chỉ chạy khi `confirmed=true`. |
| arXiv / company policy | `../transcripts/v3_openrouter_ui_20261110T112629096222.transcript.json`; `tools.yaml` | `policy` tra cứu được quy tắc nội bộ về cách chọn tool. Công cụ arXiv đã được cấu hình nhưng chưa có lượt gọi trong transcript. | Không xem nội dung policy tĩnh là tin mới; cần chạy một truy vấn arXiv để xác nhận công cụ hoạt động end-to-end. |
| UI | `../app.py`; `../transcripts/v3_openrouter_ui_20261110T112629096222.transcript.json` | Streamlit cho chọn phiên bản, chat qua tool loop, xem trạng thái hỏi lại và tải transcript; transcript xác nhận chat UI đã chạy với tool. | Tunnel công khai có thể đổi/ngừng khi restart; cần API key/quota hợp lệ. `send` yêu cầu xác nhận trước khi gửi. |
| Tool unit tests (`tests/`) | `pytest` output (`tests/test_tool_*.py`, `tests/test_tools_todo.py`) | **112 passed, 0 failed, 0 skipped**. Mỗi tool mới (wikipedia, hackernews, github_repos, calculator) có ≥ 3 test, chạy offline bằng `fake_http`. | Test mock HTTP nên không phát hiện được việc API thật đổi format; cần eval/transcript live để bù. |

## B6. Reflection

- **`system_prompt.md`:** quy định hành vi: hỏi lại khi thiếu thông tin, xin xác nhận trước khi gửi và từ chối yêu cầu ngoài phạm vi.
- **`tools.yaml`:** quy định cách chọn tool và schema/giá trị tham số để định tuyến, chẳng hạn `wikipedia`, `hackernews` và `calculator`.
- **Cần review thủ công:** tool lỗi nhưng agent vẫn đưa ra câu trả lời nghe có vẻ đúng (ví dụ calculator lỗi nhưng tự tính tiếp); chấm điểm tool call không đủ để xác nhận câu trả lời trung thực.
- **Cải thiện tiếp:** hoàn thiện calculator, làm rõ lỗi tool trong câu trả lời và bổ sung eval cho lỗi API/tool cùng chất lượng nội dung.

## B7. Small Local Model Challenge (bonus)

Nhóm không làm bonus này.
