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

## D4 — Câu hỏi mẫu & Eval Cases (gửi doanlong9304 cho `data/eval_group.json` và `REPORT.md` Phần A3)

### Câu hỏi mẫu cho REPORT Phần A3
1. *"Kiến trúc Transformer trong deep learning là gì? Tóm tắt định nghĩa từ Wikipedia giúp mình."* → route tới `wikipedia(topic="Transformer (deep learning architecture)", lang="en")`
2. *"Alan Turing là ai? Cho mình thông tin tiểu sử tóm tắt trên Wikipedia."* → route tới `wikipedia(topic="Alan Turing")`
3. *"Giải thích khái niệm Retrieval-Augmented Generation (RAG) theo Wikipedia tiếng Anh."* → route tới `wikipedia(topic="Retrieval-augmented generation", lang="en")`

### JSON snippet mẫu cho `data/eval_group.json`
```json
{
  "id": "G_wiki_single_definition",
  "phase": "B",
  "suite": "group",
  "query": "Alan Turing là ai? Tra cứu tóm tắt tiểu sử trên Wikipedia tiếng Anh giúp mình.",
  "failure_type": "wrong_tool",
  "expect": {
    "tool_calls": [
      {
        "name": "wikipedia",
        "args": {
          "topic": "Alan Turing",
          "lang": "en"
        }
      }
    ]
  },
  "metadata": {
    "skill": "routing_wikipedia_summary",
    "difficulty": "easy",
    "what_it_tests": "Hỏi tiểu sử/khái niệm bách khoa trên Wikipedia -> gọi tool wikipedia thay vì lookup."
  }
}
```

Sau đó chạy: `pytest tests/test_tool_contract.py tests/test_tool_wikipedia.py`
