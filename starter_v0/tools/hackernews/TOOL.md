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

Tìm story trên Hacker News theo từ khóa (thảo luận cộng đồng dev/tech).

Owner: thdanhnguyen

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: hackernews
    description: "TODO: làm gì. Dùng khi ... Không dùng khi ..."
    parameters:
      type: object
      properties:
        query: {type: string, description: "TODO"}
        sort: {type: string, enum: [relevance, date], default: "relevance", description: "TODO"}
        limit: {type: integer, default: 5, description: "TODO"}
      required: [query]
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_hackernews.py`
