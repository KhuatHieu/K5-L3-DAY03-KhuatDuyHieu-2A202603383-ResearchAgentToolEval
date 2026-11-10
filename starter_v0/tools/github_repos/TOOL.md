---
name: github_repos
track: bonus
kind: live_api
provider: GitHub
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# github_repos

Tìm repository trên GitHub theo từ khóa (tên, mô tả, số sao, ngôn ngữ, link).

Owner: HViettt

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: github_repos
    description: "TODO: làm gì. Dùng khi ... Không dùng khi ..."
    parameters:
      type: object
      properties:
        query: {type: string, description: "TODO"}
        sort: {type: string, enum: [stars, updated], default: "stars", description: "TODO"}
        limit: {type: integer, default: 5, description: "TODO"}
      required: [query]
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_github_repos.py`
