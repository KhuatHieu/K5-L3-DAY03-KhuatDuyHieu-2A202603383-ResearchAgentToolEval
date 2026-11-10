---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia
requires_env: []
inputs: [topic, lang]
outputs: [title, summary, url]
side_effect: false
---
# wikipedia

Lấy tóm tắt bách khoa (định nghĩa, background) của một khái niệm/người/tổ chức từ Wikipedia.

Owner: thdanhnguyen

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: wikipedia
    description: "TODO: làm gì. Dùng khi ... Không dùng khi ..."
    parameters:
      type: object
      properties:
        topic: {type: string, description: "TODO"}
        lang: {type: string, enum: [en, vi], default: "en", description: "TODO"}
      required: [topic]
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_wikipedia.py`
