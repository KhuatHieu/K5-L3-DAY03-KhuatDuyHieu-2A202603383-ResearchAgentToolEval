---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News (Algolia)
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hackernews

Tìm story và thảo luận cộng đồng dev/tech/startup trên Hacker News (Y Combinator) theo từ khóa.


## D4 — Câu hỏi mẫu & Eval Cases (gửi doanlong9304 cho `data/eval_group.json` và `REPORT.md` Phần A3)

### Câu hỏi mẫu cho REPORT Phần A3
1. *"Cộng đồng trên Hacker News đang thảo luận gì về Claude Code?"* → route tới `hackernews(query="Claude Code")`
2. *"Tìm 5 bài đăng mới nhất trên Hacker News về ngôn ngữ lập trình Rust."* → route tới `hackernews(query="Rust", sort="date", limit=5)`
3. *"Các bài viết nổi bật nhất trên HN bàn về SQLite trong production là gì?"* → route tới `hackernews(query="SQLite", sort="relevance")`

### JSON snippet mẫu cho `data/eval_group.json`
```json
{
  "id": "G_hn_single_search",
  "phase": "B",
  "suite": "group",
  "query": "Tìm 5 bài thảo luận mới nhất trên Hacker News về ngôn ngữ Rust.",
  "failure_type": "wrong_tool",
  "expect": {
    "tool_calls": [
      {
        "name": "hackernews",
        "args": {
          "query": "Rust",
          "sort": "date",
          "limit": 5
        }
      }
    ]
  },
  "metadata": {
    "skill": "routing_hackernews_search",
    "difficulty": "medium",
    "what_it_tests": "Tìm thảo luận trên Hacker News mới nhất với số lượng 5 -> gọi hackernews(query='Rust', sort='date', limit=5)."
  }
}
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_hackernews.py`
