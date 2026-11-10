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

Lấy tóm tắt bách khoa (định nghĩa, background, tiểu sử, lịch sử) của một khái niệm, nhân vật hoặc tổ chức từ Wikipedia.

Owner: thdanhnguyen

## Khi xong — dán khối này vào CUỐI `artifacts/tools.yaml`

```yaml
  - name: wikipedia
    description: "Lấy tóm tắt bách khoa (định nghĩa, khái niệm nền tảng, tiểu sử người nổi tiếng, lịch sử tổ chức) từ Wikipedia. Dùng khi user hỏi 'X là gì', 'X là ai', hoặc cần định nghĩa/kiến thức nền chuẩn xác về một khái niệm, nhân vật, sự kiện lịch sử. KHÔNG dùng cho tin tức thời sự mới nhất hôm nay/tuần này (dùng lookup), bài đăng Twitter/X (dùng timeline/social_search), hoặc bài báo khoa học chuyên sâu trên arXiv (dùng papers)."
    parameters:
      type: object
      properties:
        topic: {type: string, description: "Tên khái niệm, thực thể, nhân vật hoặc tổ chức cần tra cứu trên Wikipedia (ví dụ: 'Transformer (deep learning architecture)', 'Alan Turing')."}
        lang: {type: string, enum: [en, vi], default: "en", description: "Ngôn ngữ Wikipedia cần tra cứu ('en' cho tiếng Anh, 'vi' cho tiếng Việt)."}
      required: [topic]
```

## Câu hỏi mẫu (routing tới `wikipedia` — gửi doanlong9304 cho D4 / eval_group.json / REPORT A3)

1. `"Kiến trúc Transformer trong học sâu là gì? Cho mình tóm tắt định nghĩa từ Wikipedia tiếng Anh."`
   - Expected call: `wikipedia(topic="Transformer", lang="en")`
2. `"Alan Turing là ai? Tra cứu tiểu sử tóm tắt trên Wikipedia giúp mình."`
   - Expected call: `wikipedia(topic="Alan Turing")`
3. `"Giải thích khái niệm Retrieval-Augmented Generation (RAG) theo Wikipedia."`
   - Expected call: `wikipedia(topic="Retrieval-augmented generation", lang="en")`

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_wikipedia.py`
