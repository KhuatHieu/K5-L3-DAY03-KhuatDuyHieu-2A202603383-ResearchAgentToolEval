---
name: calculator
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [expression]
outputs: [value]
side_effect: false
---
# calculator

Tính biểu thức số học an toàn (+ - * / ** %, ngoặc, số thập phân) — KHÔNG dùng eval(); parse bằng ast.

Owner: HViettt

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: calculator
    description: "TODO: làm gì. Dùng khi ... Không dùng khi ..."
    parameters:
      type: object
      properties:
        expression: {type: string, description: "TODO"}
      required: [expression]
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_calculator.py`
