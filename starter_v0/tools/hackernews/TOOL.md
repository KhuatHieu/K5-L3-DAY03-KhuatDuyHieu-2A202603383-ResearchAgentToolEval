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

Owner: thdanhnguyen

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: hackernews
    description: "Tìm các bài đăng (stories) và thảo luận của cộng đồng lập trình viên/kỹ sư/startup trên Hacker News (Y Combinator) theo từ khóa. Dùng khi user hỏi về thảo luận trên Hacker News (HN), góc nhìn cộng đồng dev/engineer về một công nghệ, ngôn ngữ lập trình, công cụ AI, hoặc tin tức nổi bật trên HN. KHÔNG dùng cho bài đăng Twitter/X (dùng social_search/timeline), tin tức báo chí phổ thông (dùng lookup), hoặc tìm mã nguồn/repository trên GitHub (dùng github_repos)."
    parameters:
      type: object
      properties:
        query: {type: string, description: "Từ khóa tìm kiếm trên Hacker News (ví dụ: 'Claude Code', 'Rust vs Go', 'SQLite')."}
        sort: {type: string, enum: [relevance, date], default: "relevance", description: "Cách sắp xếp: 'relevance' cho bài nổi bật/liên quan nhất, 'date' cho bài mới đăng gần đây nhất."}
        limit: {type: integer, default: 5, description: "Số lượng story tối đa cần lấy (mặc định 5)."}
      required: [query]
```

## Câu hỏi mẫu (routing tới `hackernews` — gửi doanlong9304 cho D4 / eval_group.json / REPORT A3)

1. `"Cộng đồng trên Hacker News đang thảo luận gì về Claude Code?"`
   - Expected call: `hackernews(query="Claude Code")`
2. `"Tìm 5 bài đăng mới nhất trên Hacker News về ngôn ngữ lập trình Rust."`
   - Expected call: `hackernews(query="Rust", sort="date", limit=5)`
3. `"Các bài viết nổi bật nhất trên HN bàn về SQLite trong production là gì?"`
   - Expected call: `hackernews(query="SQLite", sort="relevance")`

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_hackernews.py`
