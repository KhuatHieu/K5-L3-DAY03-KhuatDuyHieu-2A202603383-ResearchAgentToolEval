"""Streamlit UI for the Research Agent — Tool Calling & Evaluation Studio.

Run from starter_v0/:
    streamlit run app.py
Public link (team showdown):
    cloudflared tunnel --url http://localhost:8501

Reuses the exact tool loop from chat.py, and writes transcripts/*.transcript.json
in the same format, so UI sessions count as live-chat evidence.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

# ---------------- Streamlit Page Config ----------------
st.set_page_config(
    page_title="Research Agent Studio",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROVIDERS = ["openrouter", "openai", "gemini", "anthropic", "ollama"]

# Pre-defined versions mapping
VERSION_PRESETS: dict[str, dict[str, Any]] = {
    "v0 (Baseline Starter)": {
        "label": "v0",
        "prompt": ARTIFACTS_DIR / "system_prompt_v0.md",
        "tools": ARTIFACTS_DIR / "tools_v0.yaml",
        "description": "Baseline v0: Prompt có chỉ dẫn đoán bừa, tự gửi không xác nhận, ép 1 bước. Tools mô tả mơ hồ. Đạt 65% accuracy.",
    },
    "v1 (Clarify Added — Handle Regression)": {
        "label": "v1",
        "prompt": ARTIFACTS_DIR / "system_prompt_v1.md",
        "tools": ARTIFACTS_DIR / "tools_v0.yaml",
        "description": "v1: Bỏ đoán mò, yêu cầu clarify. Gặp regression R01/M01/M03 do câu cấm invent handles. Case Acc tụt xuống 55%.",
    },
    "v1b (Handle Mapping Recovered)": {
        "label": "v1b",
        "prompt": ARTIFACTS_DIR / "system_prompt_v1b.md",
        "tools": ARTIFACTS_DIR / "tools_v0.yaml",
        "description": "v1b: Bỏ câu cấm invent handles -> phục hồi R01/M01/M03. Accuracy hồi phục lên 70%.",
    },
    "v1c (100% Routing — Softened Single Step)": {
        "label": "v1c",
        "prompt": ARTIFACTS_DIR / "system_prompt.md",
        "tools": ARTIFACTS_DIR / "tools_v0.yaml",
        "description": "v1c: Đổi 'Always finish in a single step' thành 'Consider finish...', sửa R08/R14. Routing đạt 100%, Case Acc 80%.",
    },
    "v2 (Wikipedia + HackerNews)": {
        "label": "v2",
        "prompt": ARTIFACTS_DIR / "system_prompt.md",
        "tools": ARTIFACTS_DIR / "tools.yaml",
        "description": "v2: Bổ sung 2 tool mới Wikipedia & HackerNews với WHEN/WHEN NOT chi tiết, giữ nguyên 100% routing trên base suite.",
    },
    "v2b (Current — 4 New Tools: Calc + GitHub)": {
        "label": "v2b",
        "prompt": ARTIFACTS_DIR / "system_prompt.md",
        "tools": ARTIFACTS_DIR / "tools.yaml",
        "description": "v2b: Bổ sung đủ 4 tool mới (+Calculator & GitHub Repos), hoàn thành toàn bộ test challenges và 10 eval cases nhóm.",
    },
    "Custom (Tùy chỉnh)": {
        "label": "v3",
        "prompt": ARTIFACTS_DIR / "system_prompt.md",
        "tools": ARTIFACTS_DIR / "tools.yaml",
        "description": "Tùy chỉnh đường dẫn System Prompt và Tools YAML thủ công.",
    },
}

# ---------------- Sidebar Configuration ----------------
with st.sidebar:
    st.header("⚙️ Agent Settings")

    preset_name = st.selectbox(
        "Phiên bản (Version Preset)",
        list(VERSION_PRESETS.keys()),
        index=5,  # Default to v2b (Current)
        help="Chọn giữa Baseline v0 ban đầu, các mốc v1/v1b/v1c tối ưu prompt, hoặc v2b đầy đủ tool.",
    )
    preset_data = VERSION_PRESETS[preset_name]

    if preset_name == "Custom (Tùy chỉnh)":
        version_label = st.text_input("Version label", value=preset_data["label"])
        prompt_path = Path(st.text_input("System prompt path", value=str(preset_data["prompt"])))
        tools_path = Path(st.text_input("Tools yaml path", value=str(preset_data["tools"])))
    else:
        version_label = preset_data["label"]
        prompt_path = preset_data["prompt"]
        tools_path = preset_data["tools"]
        st.caption(f"ℹ️ *{preset_data['description']}*")

    st.markdown("---")
    st.subheader("🤖 Model & Provider")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (trống = default của provider)", value="") or None

    api_key_override = st.text_input(
        f"API Key Override ({provider_name.upper()})",
        type="password",
        help="Nếu key trong .env hết hạn (hoặc lỗi 429), nhập key trực tiếp tại đây để chạy.",
    )
    if api_key_override:
        env_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        if provider_name in env_map:
            os.environ[env_map[provider_name]] = api_key_override

    st.markdown("---")
    st.subheader("🎛️ Tool Loop Parameters")
    max_rounds = st.slider("Max tool rounds", 1, 8, 4)
    history_window = st.slider("History window (cặp turns)", 0, 10, 5)
    show_tools = st.checkbox("Hiện chi tiết Tool Calls", value=True)

    st.markdown("---")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🗑️ New Chat", use_container_width=True):
            for k in ("messages", "history", "transcript", "transcript_path"):
                st.session_state.pop(k, None)
            st.rerun()

    with col_sb2:
        if "transcript" in st.session_state and st.session_state.transcript.get("turns"):
            transcript_json = json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 Log JSON",
                data=transcript_json,
                file_name=f"{st.session_state.transcript_path.name}",
                mime="application/json",
                use_container_width=True,
            )


@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def init_transcript() -> tuple[dict[str, Any], Path]:
    artifact_version = build_artifact_version(version_label, prompt_path, tools_path)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join([safe_slug(version_label), safe_slug(provider_name), "ui", stamp])
    path = ROOT / "transcripts" / f"{tid}.transcript.json"
    transcript = {
        "transcript_id": tid,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "source": "streamlit",
        "system_prompt": str(prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return transcript, path


# Initialize session states
st.session_state.setdefault("messages", [])
st.session_state.setdefault("history", [])
if "transcript" not in st.session_state:
    st.session_state.transcript, st.session_state.transcript_path = init_transcript()

# Reset transcript if version label changed
if st.session_state.transcript.get("version") != version_label:
    st.session_state.transcript, st.session_state.transcript_path = init_transcript()

# ---------------- Main Title & Navigation ----------------
st.title("🔎 Research Agent Studio")
st.markdown(
    f"**Active Config:** Version: `{version_label}` · Provider: `{provider_name}` · Model: `{model or 'default'}` · Transcript: `{st.session_state.transcript_path.name}`"
)

# Render main tabs
tab_chat, tab_versions, tab_prompts, tab_v0_analysis, tab_v1_analysis, tab_tools, tab_report = st.tabs([
    "💬 Live Chat Agent",
    "📊 Version Evidence (v0 → v3)",
    "📜 Full Prompts Evolution",
    "🔍 v0 Baseline Analysis",
    "🔬 v1 Iterations (v1, v1b, v1c)",
    "🛠️ Tool Registry (14 Tools)",
    "📑 Project Report & Showdown",
])


# ==============================================================================
# TAB 1: LIVE CHAT AGENT
# ==============================================================================
with tab_chat:
    # Full prompt inspection toggle for active session
    curr_active_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    with st.expander(f"📜 Xem toàn bộ System Prompt đang dùng (Phiên bản: {version_label})", expanded=False):
        c_pm1, c_pm2 = st.columns([3, 1])
        with c_pm1:
            st.code(curr_active_prompt, language="markdown")
        with c_pm2:
            st.caption("Thông tin Prompt:")
            st.markdown(f"- **Đường dẫn:** `{prompt_path.name}`")
            st.markdown(f"- **Số từ:** `{len(curr_active_prompt.split())} từ`")
            st.markdown(f"- **Số ký tự:** `{len(curr_active_prompt)} ký tự`")
            st.markdown(f"- **SHA-256:** `{hashlib.sha256(curr_active_prompt.encode('utf-8')).hexdigest()[:12]}`")

    st.subheader("💡 Câu hỏi mẫu (Quick Prompts)")

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        st.markdown("**⚠️ Test bẫy v0 & Regression v1**")
        if st.button("👤 Tweet mới nhất của Elon Musk?", use_container_width=True, help="Test v1 regression: v1 từ chối map handle elonmusk; v1b/v1c map đúng"):
            st.session_state["queued_query"] = "Tweet mới nhất của Elon Musk là gì?"
            st.rerun()
        if st.button("🔗 Tóm tắt bài viết này (Thiếu URL)", use_container_width=True, help="Thiếu URL -> v0 đoán mò; v1/v1b/v1c gọi clarify hỏi link"):
            st.session_state["queued_query"] = "Tóm tắt bài viết này giúp mình với."
            st.rerun()
        if st.button("💻 Viết code Python đọc CSV", use_container_width=True, help="Out-of-scope: v0/v1/v1b bị ép gọi tool format; v1c trả lời trực tiếp / no_tool"):
            st.session_state["queued_query"] = "Viết giúp mình một hàm Python đọc file CSV bằng pandas."
            st.rerun()

    with col_q2:
        st.markdown("**🔎 Tra cứu & Nghiên cứu thông tin**")
        if st.button("📰 Tin AI hôm nay có gì mới?", use_container_width=True):
            st.session_state["queued_query"] = "Tin tức AI hôm nay có gì nổi bật?"
            st.rerun()
        if st.button("🐦 Tweet mới nhất của Sam Altman", use_container_width=True):
            st.session_state["queued_query"] = "Tweet mới nhất của Sam Altman là gì?"
            st.rerun()
        if st.button("✉️ Gửi Telegram (Cần xác nhận)", use_container_width=True):
            st.session_state["queued_query"] = "Gửi thông điệp này lên Telegram: 'Hệ thống đã cập nhật xong'"
            st.rerun()

    with col_q3:
        st.markdown("**🚀 Thử 4 Tool mới nhóm tự thêm**")
        if st.button("📚 Wikipedia: Artificial Intelligence", use_container_width=True):
            st.session_state["queued_query"] = "Tra cứu Wikipedia tóm tắt về Artificial Intelligence"
            st.rerun()
        if st.button("📰 HackerNews: Tin nóng về LLM", use_container_width=True):
            st.session_state["queued_query"] = "Tìm tin tức công nghệ mới nhất trên HackerNews về LLMs"
            st.rerun()
        if st.button("💻 GitHub: Tìm repo agent phổ biến", use_container_width=True):
            st.session_state["queued_query"] = "Tìm 5 repository GitHub nhiều sao nhất về LLM Agents"
            st.rerun()
        if st.button("🧮 Calculator: (150 * 4) + 250 / 5", use_container_width=True):
            st.session_state["queued_query"] = "Tính toán biểu thức toán học: (150 * 4) + 250 / 5"
            st.rerun()

    st.markdown("---")

    # Render tool events helper
    def render_tool_events(rounds: list[dict[str, Any]]) -> None:
        for rnd in rounds:
            round_num = rnd.get("round", 1)
            tool_calls = rnd.get("tool_calls", [])
            tool_results = rnd.get("tool_results", [])
            results_by_call_id = {tr.get("call_id"): tr for tr in tool_results}

            with st.expander(f"🔧 Round {round_num}: {len(tool_calls)} Tool Call(s)", expanded=False):
                for tc in tool_calls:
                    cid = tc.get("id")
                    name = tc.get("name")
                    args = tc.get("args", {})
                    res_obj = results_by_call_id.get(cid, {})

                    st.markdown(f"**Tool:** `{name}`")
                    c_arg, c_res = st.columns(2)
                    with c_arg:
                        st.caption("📥 Arguments")
                        st.json(args)
                    with c_res:
                        st.caption("📤 Result")
                        st.json(res_obj.get("result", {}))

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if show_tools and msg.get("rounds"):
                render_tool_events(msg["rounds"])
            st.markdown(msg["content"])

    # Check for queued action confirmation for 'send'
    last_assistant_turn = None
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_assistant_turn = st.session_state.messages[-1]
        text_lower = last_assistant_turn["content"].lower()
        if any(w in text_lower for w in ["xác nhận", "confirm", "bạn có muốn gửi", "gửi đi không"]):
            st.info("⚠️ **Agent đang yêu cầu bạn xác nhận hành động gửi tin:**")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("✅ Đồng ý gửi (Xác nhận)", use_container_width=True, key="btn_confirm_send"):
                    st.session_state["queued_query"] = "Có, tôi xác nhận gửi nội dung này."
                    st.rerun()
            with col_act2:
                if st.button("❌ Không gửi (Hủy bỏ)", use_container_width=True, key="btn_cancel_send"):
                    st.session_state["queued_query"] = "Không, tôi không muốn gửi."
                    st.rerun()

    # User input bar
    queued_input = st.session_state.pop("queued_query", None)
    chat_input = st.chat_input("Hỏi agent… (vd: Tin AI mới nhất tuần này?)")
    user_text = queued_input or chat_input

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        system_prompt = prompt_path.read_text(encoding="utf-8")
        tools = to_openai_tools(load_tool_declarations(tools_path))
        messages = [
            {"role": "system", "content": system_prompt},
            *trim_history(st.session_state.history, history_window),
            {"role": "user", "content": user_text},
        ]
        turn: dict[str, Any] = {
            "turn_index": len(st.session_state.transcript["turns"]) + 1,
            "started_at": now_iso(),
            "user": user_text,
        }

        with st.chat_message("assistant"):
            with st.spinner(f"Agent đang xử lý (version={version_label})…"):
                try:
                    result = run_model_tool_loop(
                        provider=get_provider(provider_name),
                        messages=messages,
                        tools=tools,
                        model=model,
                        max_tool_rounds=max_rounds,
                    )
                    answer = result.get("assistant_text") or "(không có câu trả lời)"
                    turn.update(result)
                except Exception as exc:
                    result = {"rounds": []}
                    answer = f"❌ {type(exc).__name__}: {exc}"
                    turn.update({"status": "provider_error", "error": answer})

            if show_tools and result.get("rounds"):
                render_tool_events(result["rounds"])

            if result.get("status") == "waiting_for_user":
                st.warning("🔔 **Agent đang hỏi lại bạn (clarify)** — vui lòng trả lời hoặc bổ sung thông tin ở ô chat bên dưới.")

            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer, "rounds": result.get("rounds", [])})
        if turn.get("status") != "provider_error":
            st.session_state.history += [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer},
            ]
        turn["ended_at"] = now_iso()
        st.session_state.transcript["turns"].append(turn)
        write_transcript(st.session_state.transcript_path, st.session_state.transcript)
        st.rerun()


# ==============================================================================
# TAB 2: VERSION EVIDENCE (v0 → v3)
# ==============================================================================
with tab_versions:
    st.header("📊 Quá trình Tối ưu hóa & Đánh giá (v0 → v3)")
    st.markdown("Toàn bộ chu kỳ lặp được dẫn dắt bởi bằng chứng (evidence-driven iteration), ghi nhận đầy đủ tại `artifacts/version_log.csv`.")

    # Metric KPI Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="🎯 Case Accuracy", value="80.0%", delta="+15.0% vs v0 (65%)")
    with col_m2:
        st.metric(label="🧭 Routing Accuracy", value="95.0% - 100%", delta="+15.0% vs v0 (80%)")
    with col_m3:
        st.metric(label="⚙️ Args Accuracy", value="80.0%", delta="+15.0% vs v0 (65%)")
    with col_m4:
        st.metric(label="🔄 Multiturn Accuracy", value="83.3%", delta="Duy trì ổn định")

    st.markdown("---")

    # Accuracy progression chart
    st.subheader("📈 Biểu đồ Tăng trưởng Độ chính xác qua các Phiên bản")
    perf_data = pd.DataFrame({
        "Version": ["v0 (Baseline)", "v1", "v1b", "v1c", "v2", "v2b (Current)"],
        "Case Accuracy (%)": [65.0, 55.0, 70.0, 80.0, 80.0, 80.0],
        "Routing Accuracy (%)": [80.0, 85.0, 90.0, 100.0, 100.0, 95.0],
        "Args Accuracy (%)": [65.0, 55.0, 70.0, 80.0, 80.0, 80.0],
    }).set_index("Version")
    st.line_chart(perf_data)

    st.markdown("---")
    st.subheader("📋 Bảng Nhật ký Phiên bản (`version_log.csv`)")

    vlog_path = ARTIFACTS_DIR / "version_log.csv"
    if vlog_path.exists():
        df_vlog = pd.read_csv(vlog_path)
        st.dataframe(
            df_vlog[["version", "author", "changed_artifact", "hypothesis", "metric_before", "metric_after", "run_file"]],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("🔍 Xem chi tiết lý do và phân tích từng phiên bản"):
            for _, row in df_vlog.iterrows():
                st.markdown(f"### 🏷️ `{row['version']}` — {row['changed_artifact']} (Tác giả: {row['author']})")
                st.markdown(f"- **Giả thuyết:** {row['hypothesis']}")
                st.markdown(f"- **Metric Trước ➔ Sau:** `{row['metric_before']}` ➔ `{row['metric_after']}`")
                st.markdown(f"- **Kết quả chi tiết:** {row['reason']}")
                st.markdown(f"- **Run file:** `{row['run_file']}`")
                st.markdown("---")
    else:
        st.warning("Chưa tìm thấy file `version_log.csv`.")


# ==============================================================================
# TAB 3: FULL PROMPTS EVOLUTION (v0 → v3)
# ==============================================================================
with tab_prompts:
    st.header("📜 Toàn bộ System Prompts qua các Phiên bản (Full Prompts)")
    st.markdown("""
    Khám phá toàn văn, cấu trúc chi tiết, và sự thay đổi từng dòng chữ của System Prompt từ bản **v0 Baseline** đến **v1c / v2 / v2b**.
    Mỗi thay đổi đều giải quyết một điểm yếu cụ thể trong hành vi ra quyết định của Agent.
    """)

    # Load all prompts
    all_prompts = {
        "v0 (Baseline)": {
            "path": ARTIFACTS_DIR / "system_prompt_v0.md",
            "tag": "❌ Anti-patterns & Guessing",
            "role": "fast, proactive",
            "clarify_rule": "❌ Cấm hỏi lại ('hates being asked questions'), tự đoán Sam Altman hoặc URL bừa bãi",
            "send_rule": "❌ Tự gửi ngay lập tức ('just go ahead and do it')",
            "step_rule": "❌ Ép 1 bước cứng nhắc ('Always finish in a single step. Pick one tool')",
            "acc": "65%",
            "routing": "80%",
        },
        "v1 (Clarify Added)": {
            "path": ARTIFACTS_DIR / "system_prompt_v1.md",
            "tag": "⚠️ Clarify Added (Handle Regression)",
            "role": "fast, proactive",
            "clarify_rule": "✅ Bắt buộc gọi clarify khi thiếu info. ❌ Thêm câu quá chặt: 'Never invent account handles or URLs'",
            "send_rule": "✅ Chặn tự gửi, chỉ gửi khi confirmed=true",
            "step_rule": "❌ Vẫn ép 1 bước cứng nhắc",
            "acc": "55%",
            "routing": "85%",
        },
        "v1b (Handle Restored)": {
            "path": ARTIFACTS_DIR / "system_prompt_v1b.md",
            "tag": "🔄 Handle Mapping Recovered",
            "role": "fast, proactive",
            "clarify_rule": "✅ Bắt buộc gọi clarify. ✅ Xóa bỏ câu cấm invent handles ➔ Phục hồi mapping tên người sang handle",
            "send_rule": "✅ Chỉ gửi khi có xác nhận",
            "step_rule": "❌ Vẫn ép 1 bước cứng nhắc (vướng out-of-scope)",
            "acc": "70%",
            "routing": "90%",
        },
        "v1c / v2 / v2b (Final)": {
            "path": ARTIFACTS_DIR / "system_prompt.md",
            "tag": "🏆 100% Routing Accuracy",
            "role": "professional, proactive",
            "clarify_rule": "✅ Bắt buộc gọi clarify khi thiếu info",
            "send_rule": "✅ Chỉ gửi khi confirmed=true",
            "step_rule": "✅ Làm mềm: 'Consider finish the request in a single step' (cho phép no_tool cho out-of-scope)",
            "acc": "80%",
            "routing": "100%",
        },
    }

    # High-level summary of prompt components
    st.subheader("📑 4 Thành phần Cốt lõi của System Prompt")
    c_cmp1, c_cmp2, c_cmp3, c_cmp4 = st.columns(4)
    with c_cmp1:
        st.markdown("**1. Định hình Persona**")
        st.caption("Từ `fast` (hấp tấp, đoán bừa) ➔ `professional` (chuyên nghiệp, chuẩn mực).")
    with c_cmp2:
        st.markdown("**2. Xử lý Thiếu Thông tin**")
        st.caption("Từ ép đoán `@sama`/URL ➔ bắt buộc gọi tool `clarify` một câu ngắn gọn rồi dừng chờ.")
    with c_cmp3:
        st.markdown("**3. Biên An toàn Gửi tin**")
        st.caption("Từ tự ý gửi ➔ bắt buộc hiển thị nội dung và yêu cầu xác nhận `confirmed=true`.")
    with c_cmp4:
        st.markdown("**4. Ranh giới Gọi Tool**")
        st.caption("Từ ép 'Pick one tool' ➔ 'Consider finish...' cho phép từ chối gọi tool cho câu ngoài phạm vi.")

    st.markdown("---")

    # 4-Column Side-by-Side Full Prompts Display
    st.subheader("👀 Hiển thị Toàn văn 4 Phiên bản Cạnh nhau (Side-by-Side Grid)")

    cols_full = st.columns(4)
    for col, (v_name, v_info) in zip(cols_full, all_prompts.items()):
        with col:
            st.markdown(f"#### {v_name}")
            st.caption(f"**Trạng thái:** {v_info['tag']}")
            st.caption(f"**Chỉ số:** Case Acc `{v_info['acc']}` · Routing `{v_info['routing']}`")
            p_text = v_info["path"].read_text(encoding="utf-8") if v_info["path"].exists() else "File not found"
            st.text_area(f"Full text ({v_name})", value=p_text, height=350, disabled=True, key=f"txt_full_{v_name}")

            with st.expander("🔍 Chi tiết cấu trúc", expanded=False):
                st.markdown(f"- **Persona:** `{v_info['role']}`")
                st.markdown(f"- **Hỏi lại:** {v_info['clarify_rule']}")
                st.markdown(f"- **Gửi tin:** {v_info['send_rule']}")
                st.markdown(f"- **Số bước:** {v_info['step_rule']}")

    st.markdown("---")

    # Interactive Diff Tool
    st.subheader("⚖️ So sánh Trực quan Diff giữa 2 Phiên bản Bất kỳ")
    c_diff_sel1, c_diff_sel2 = st.columns(2)
    with c_diff_sel1:
        diff_ver_a = st.selectbox("Chọn Phiên bản A (Gốc):", list(all_prompts.keys()), index=0)
    with c_diff_sel2:
        diff_ver_b = st.selectbox("Chọn Phiên bản B (So sánh):", list(all_prompts.keys()), index=3)

    if diff_ver_a and diff_ver_b:
        text_a = all_prompts[diff_ver_a]["path"].read_text(encoding="utf-8").splitlines(keepends=True)
        text_b = all_prompts[diff_ver_b]["path"].read_text(encoding="utf-8").splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(text_a, text_b, fromfile=diff_ver_a, tofile=diff_ver_b))
        if diff_lines:
            st.code("".join(diff_lines), language="diff")
        else:
            st.success("Hai phiên bản prompt này có nội dung hoàn toàn giống nhau.")


# ==============================================================================
# TAB 4: v0 BASELINE & FAILURE ANALYSIS
# ==============================================================================
with tab_v0_analysis:
    st.header("🔍 Phân tích Chi tiết Lỗi ở Baseline v0")
    st.markdown("""
    Baseline **v0** đạt độ chính xác **65% (13/20 passed)** trên bộ đánh giá `eval_base.json`.
    Các lỗi nghiêm trọng xuất phát từ các **chỉ dẫn xấu có chủ đích** trong System Prompt và mô tả mơ hồ trong `tools.yaml`.
    """)

    st.subheader("❌ 7 Test Case Thất bại ở v0 và Giải pháp Khắc phục")

    v0_failures = [
        {
            "Case ID": "R10_missing_handle",
            "Loại lỗi": "missing_info",
            "Hành vi v0 (Sai)": "Tự đoán tài khoản @sama và gọi timeline",
            "Kỳ vọng đúng": "Gọi clarify để hỏi người dùng muốn xem bài của ai",
            "Chỉ dẫn xấu v0": "'If a request mentions a tweet but doesn't say whose, pick a well-known account like Sam Altman.'",
            "Khắc phục ở v1": "Bỏ đoán mò; bắt buộc gọi clarify khi thiếu thông tin bắt buộc.",
        },
        {
            "Case ID": "R11_missing_url",
            "Loại lỗi": "missing_info",
            "Hành vi v0 (Sai)": "Tự bịa URL (openai.com) và gọi fetch",
            "Kỳ vọng đúng": "Gọi clarify để hỏi URL bài viết",
            "Chỉ dẫn xấu v0": "'If you only have a vague reference like \"this article\", assume a likely URL and read it.'",
            "Khắc phục ở v1": "Bỏ chỉ dẫn tự đoán URL; yêu cầu clarify URL cụ thể.",
        },
        {
            "Case ID": "R12_confirm_before_send",
            "Loại lỗi": "wrong_boundary",
            "Hành vi v0 (Sai)": "Tự động gọi send với confirmed=true",
            "Kỳ vọng đúng": "Hỏi xác nhận người dùng trước khi gửi (confirmed=false)",
            "Chỉ dẫn xấu v0": "'When user wants to send... just go ahead and do it so they don't have to wait.'",
            "Khắc phục ở v1": "Thiết lập ranh giới an toàn: chỉ gọi send khi có xác nhận tường minh.",
        },
        {
            "Case ID": "R14_out_of_scope_coding",
            "Loại lỗi": "out_of_scope",
            "Hành vi v0 (Sai)": "Bị ép gọi format tool cho câu hỏi viết code Python",
            "Kỳ vọng đúng": "no_tool (không gọi bất kỳ tool nào, trả lời trực tiếp)",
            "Chỉ dẫn xấu v0": "'Always finish the request in a single step. Pick one tool and fill in arguments.'",
            "Khắc phục ở v1c": "Đổi thành 'Consider finish...', cho phép trả lời trực tiếp không qua tool.",
        },
        {
            "Case ID": "R03_web_news_routing",
            "Loại lỗi": "wrong_arg_value",
            "Hành vi v0 (Sai)": "query='tin tức trí tuệ nhân tạo AI hôm nay' (quá dài)",
            "Kỳ vọng đúng": "query='AI', topic='news', timeframe='day'",
            "Chỉ dẫn xấu v0": "Tools description không có quy ước trích xuất từ khóa ngắn gọn.",
            "Khắc phục ở v2": "Bổ sung arg conventions trong tools.yaml cho topic=news và timeframe.",
        },
        {
            "Case ID": "R13_parallel_web_and_tweets",
            "Loại lỗi": "wrong_tool / wrong_arg",
            "Hành vi v0 (Sai)": "Chỉ gọi lookup, thiếu lệnh gọi social_search song song",
            "Kỳ vọng đúng": "Gọi cả 2 tool lookup và social_search",
            "Chỉ dẫn xấu v0": "v0 ép chỉ chọn một tool duy nhất ('Pick one tool').",
            "Khắc phục ở v1c/v2": "Bỏ ép buộc 1 tool đơn lẻ, hỗ trợ multi-tool execution.",
        },
        {
            "Case ID": "M02_carryover_timeframe",
            "Loại lỗi": "wrong_arg_value",
            "Hành vi v0 (Sai)": "query mang theo chuỗi thời gian thừa",
            "Kỳ vọng đúng": "query='robotics', timeframe='week'",
            "Chỉ dẫn xấu v0": "Không hướng dẫn tách từ khóa chính khỏi modifier thời gian.",
            "Khắc phục ở v2": "Quy định rõ ràng cấu trúc query trong tool lookup.",
        },
    ]

    st.dataframe(pd.DataFrame(v0_failures), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⚖️ So sánh Trực quan System Prompt (v0 vs Hiện tại)")

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.markdown("#### ❌ Prompt v0 (Chứa bẫy / Anti-patterns)")
        v0_prompt_text = (ARTIFACTS_DIR / "system_prompt_v0.md").read_text(encoding="utf-8") if (ARTIFACTS_DIR / "system_prompt_v0.md").exists() else "N/A"
        st.code(v0_prompt_text, language="markdown")
    with c_p2:
        st.markdown("#### ✅ Prompt Hiện tại (Đã chuẩn hóa & Khắc phục)")
        curr_prompt_text = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        st.code(curr_prompt_text, language="markdown")

    st.markdown("---")
    st.subheader("📊 Bảng 20 Test Cases Đánh giá ở Baseline v0")

    run_v0_path = ROOT / "runs" / "v0_B_base_openai_20261110T095815539037.json"
    if run_v0_path.exists():
        v0_run_data = json.loads(run_v0_path.read_text(encoding="utf-8"))
        results_rows = []
        for r in v0_run_data.get("results", []):
            res = r.get("result", {})
            actual_calls = res.get("actual_tool_calls") or []
            results_rows.append({
                "Case ID": r.get("id"),
                "Multiturn": r.get("is_multiturn"),
                "Loại kiểm tra": r.get("metadata", {}).get("skill", ""),
                "Passed": "✅ PASS" if res.get("passed") else "❌ FAIL",
                "Actual Tool": "|".join(c.get("name", "") for c in actual_calls) or "no_tool",
                "Lỗi quan sát": "; ".join(res.get("failures") or []) or "None",
            })
        st.dataframe(pd.DataFrame(results_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 5: v1 ITERATIONS & PROMPT TUNING (v1, v1b, v1c)
# ==============================================================================
with tab_v1_analysis:
    st.header("🔬 Quá trình Tinh chỉnh Prompt v1 (v1 ➔ v1b ➔ v1c)")
    st.markdown("""
    Giai đoạn **v1** tập trung hoàn toàn vào việc sửa đổi `system_prompt.md` nhằm loại bỏ các bẫy có sẵn của v0,
    **giữ nguyên công cụ ban đầu** (`tools_hash: 8db0ba629f52`).
    Đây là ví dụ kinh điển về chu trình: **Sửa bẫy ➔ Gặp Regression ➔ Cô lập nguyên nhân ➔ Đạt Đỉnh Routing 100%**.
    """)

    # 3-column KPI comparison
    col_v1, col_v1b, col_v1c = st.columns(3)
    with col_v1:
        st.markdown("### ⚠️ v1: Clarify & Regression")
        st.metric("Case Accuracy", "55.0%", delta="-10.0% vs v0 (65%)", delta_color="inverse")
        st.metric("Routing Accuracy", "85.0%", delta="+5.0% vs v0")
        st.caption("✅ **Khắc phục:** `R10` (missing handle) & `R11` (missing url) đã gọi clarify.")
        st.caption("❌ **Regression:** `R01`, `M01`, `M03` fail do câu cấm invent handles khiến model không dám map tên người thành handle.")

    with col_v1b:
        st.markdown("### 🔄 v1b: Phục hồi Handle Mapping")
        st.metric("Case Accuracy", "70.0%", delta="+15.0% vs v1")
        st.metric("Routing Accuracy", "90.0%", delta="+5.0% vs v1")
        st.caption("✅ **Thay đổi duy nhất:** Bỏ câu *'Never invent account handles or URLs'*.")
        st.caption("🎯 **Kết quả:** Phục hồi thành công `R01`, `M01`, `M03`. Còn vướng `R08`, `R14` (out_of_scope).")

    with col_v1c:
        st.markdown("### 🏆 v1c: 100% Routing Milestone")
        st.metric("Case Accuracy", "80.0%", delta="+10.0% vs v1b")
        st.metric("Routing Accuracy", "100.0%", delta="+10.0% (20/20 cases)")
        st.caption("✅ **Thay đổi:** Đổi *'Always finish in a single step'* ➔ *'Consider finish...'*, đổi *'fast'* ➔ *'professional'*.")
        st.caption("🎉 **Kết quả:** `R08` & `R14` pass hoàn hảo với `no_tool`. Đạt 100% routing!")

    st.markdown("---")

    # Interactive sub-version drilldown
    st.subheader("🔍 Chi tiết Từng Bước Tinh chỉnh trong v1")
    v1_choice = st.radio(
        "Chọn phiên bản để soi sâu chi tiết:",
        ["v1 (Sửa bẫy + Gặp regression)", "v1b (Phục hồi handle mapping)", "v1c (Soften single-step ➔ 100% routing)"],
        horizontal=True,
    )

    v1_files_map = {
        "v1 (Sửa bẫy + Gặp regression)": {
            "file": "v1_B_base_openai_20261110T101417806341.json",
            "prompt_file": ARTIFACTS_DIR / "system_prompt_v1.md",
            "key_learning": "Thêm luật quá chặt ('Never invent account handles or URLs') khiến LLM từ chối suy luận tri thức thông thường (Sam Altman -> @sama, Elon Musk -> @elonmusk).",
            "fails_count": 9,
        },
        "v1b (Phục hồi handle mapping)": {
            "file": "v1b_B_base_openai_20261110T101547908400.json",
            "prompt_file": ARTIFACTS_DIR / "system_prompt_v1b.md",
            "key_learning": "Chỉ một câu bị xóa đã cứu sống 3 test case quan trọng và tăng 15% accuracy. Minh chứng cho việc tối ưu từng thay đổi nhỏ (single hypothesis).",
            "fails_count": 6,
        },
        "v1c (Soften single-step ➔ 100% routing)": {
            "file": "v1c_B_base_openai_20261110T101922117035.json",
            "prompt_file": ARTIFACTS_DIR / "system_prompt.md",
            "key_learning": "Cụm từ 'Always finish in a single step. Pick one tool' là thủ phạm ép LLM phải gọi tool dù câu hỏi hoàn toàn ngoài phạm vi (như viết code Python). Làm mềm nó thành 'Consider finish...' lập tức đưa Routing Accuracy lên 100%.",
            "fails_count": 4,
        },
    }

    selected_v1 = v1_files_map[v1_choice]
    c_info1, c_info2 = st.columns([3, 2])
    with c_info1:
        st.info(f"💡 **Bài học cốt lõi:** {selected_v1['key_learning']}")
        st.markdown(f"**Run log file:** `{selected_v1['file']}` (Số case thất bại: **{selected_v1['fails_count']}/20**)")
    with c_info2:
        st.caption("📜 Nội dung System Prompt ở mốc này:")
        prompt_txt = selected_v1["prompt_file"].read_text(encoding="utf-8") if selected_v1["prompt_file"].exists() else "N/A"
        st.code(prompt_txt, language="markdown")

    # Render failures of selected version
    run_path = ROOT / "runs" / selected_v1["file"]
    if run_path.exists():
        run_data = json.loads(run_path.read_text(encoding="utf-8"))
        failed_items = [r for r in run_data.get("results", []) if not r.get("result", {}).get("passed")]
        with st.expander(f"⚠️ Xem {len(failed_items)} Test Case Thất bại của {v1_choice.split()[0]}", expanded=True):
            fail_rows = []
            for item in failed_items:
                res = item.get("result", {})
                fail_rows.append({
                    "Case ID": item.get("id"),
                    "Query": item.get("input"),
                    "Expected": item.get("expect"),
                    "Actual Tools": [c.get("name") for c in res.get("actual_tool_calls", [])] or ["no_tool"],
                    "Lỗi cụ thể": "; ".join(res.get("failures", [])),
                })
            st.dataframe(pd.DataFrame(fail_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📊 Ma trận Tiến hóa 20 Base Cases (v0 ➔ v1 ➔ v1b ➔ v1c)")
    st.caption("Theo dõi chi tiết sự chuyển biến của từng test case qua 4 mốc tinh chỉnh system prompt:")

    # Load 4 runs
    runs_paths = {
        "v0": ROOT / "runs" / "v0_B_base_openai_20261110T095815539037.json",
        "v1": ROOT / "runs" / "v1_B_base_openai_20261110T101417806341.json",
        "v1b": ROOT / "runs" / "v1b_B_base_openai_20261110T101547908400.json",
        "v1c": ROOT / "runs" / "v1c_B_base_openai_20261110T101922117035.json",
    }
    if all(p.exists() for p in runs_paths.values()):
        d_runs = {k: json.loads(p.read_text(encoding="utf-8"))["results"] for k, p in runs_paths.items()}
        matrix_rows = []
        for i in range(len(d_runs["v0"])):
            cid = d_runs["v0"][i]["id"]
            p0 = "✅ PASS" if d_runs["v0"][i]["result"]["passed"] else "❌ FAIL"
            p1 = "✅ PASS" if d_runs["v1"][i]["result"]["passed"] else "❌ FAIL"
            p1b = "✅ PASS" if d_runs["v1b"][i]["result"]["passed"] else "❌ FAIL"
            p1c = "✅ PASS" if d_runs["v1c"][i]["result"]["passed"] else "❌ FAIL"

            # Dynamic notes
            note = ""
            if cid in ("R10_missing_handle", "R11_missing_url"):
                note = "🎉 Fixed in v1 (Đã gọi clarify)"
            elif cid in ("R01_user_tweets_routing", "M01_clarify_then_fill", "M03_correction_handle"):
                note = "⚠️ Regression in v1 ➔ 🚀 Phục hồi in v1b"
            elif cid in ("R08_out_of_scope", "R14_out_of_scope_coding"):
                note = "🎯 Fixed in v1c (no_tool thành công)"
            elif cid == "R12_confirm_before_send":
                note = "⚠️ Routing đúng clarify, cần yes_no response_type"
            elif not d_runs["v1c"][i]["result"]["passed"]:
                note = "⏳ Còn vướng tham số chi tiết (xử lý ở v2)"
            else:
                note = "✅ Xanh ổn định"

            matrix_rows.append({
                "Case ID": cid,
                "Kỹ năng kiểm tra": d_runs["v0"][i].get("metadata", {}).get("skill", ""),
                "v0 (Base)": p0,
                "v1 (Clarify)": p1,
                "v1b (Handle Fix)": p1b,
                "v1c (100% Route)": p1c,
                "Đánh giá tiến trình": note,
            })
        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 6: TOOL REGISTRY (14 TOOLS)
# ==============================================================================
with tab_tools:
    st.header("🛠️ Tool Registry & Danh mục Công cụ (14 Tools)")
    st.markdown("Agent được trang bị tổng cộng 14 công cụ: 6 tool lõi, 4 tool bổ sung, và **4 tool mới do nhóm tự phát triển**.")

    tools_decl = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")

    core_tool_names = {"clarify", "timeline", "social_search", "lookup", "fetch", "format"}
    bonus_tool_names = {"send", "policy", "papers", "paper_text"}
    new_tool_names = {"wikipedia", "hackernews", "calculator", "github_repos"}

    st.markdown("### 🆕 4 Tool Mới Nhóm Tự Thêm (Đạt Bonus Point)")
    col_t1, col_t2 = st.columns(2)
    for i, t in enumerate(tools_decl):
        name = t["name"]
        if name in new_tool_names:
            target_col = col_t1 if (i % 2 == 0) else col_t2
            with target_col:
                with st.expander(f"✨ `{name}` — {t.get('description', '')[:50]}...", expanded=True):
                    st.markdown(f"**Tên:** `{name}` `[Tool mới của team]`")
                    st.markdown(f"**Mô tả:** {t.get('description')}")
                    params = t.get("parameters", {})
                    st.caption("Các tham số bắt buộc:")
                    st.code(json.dumps(params.get("required", []), indent=2), language="json")

    st.markdown("---")
    st.markdown("### 📦 Danh sách Toàn bộ 14 Tools trong Hệ thống")

    tools_table = []
    for t in tools_decl:
        name = t["name"]
        cat = "🆕 Nhóm tự thêm" if name in new_tool_names else ("🛡️ Bonus Tool" if name in bonus_tool_names else "📦 Core Tool")
        req_params = ", ".join(t.get("parameters", {}).get("required", [])) or "None"
        tools_table.append({
            "Tên Tool": name,
            "Phân loại": cat,
            "Tham số bắt buộc": req_params,
            "Mô tả tóm tắt": t.get("description", "").split(".")[0],
        })

    st.dataframe(pd.DataFrame(tools_table), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 7: PROJECT REPORT & SHOWDOWN
# ==============================================================================
with tab_report:
    st.header("📑 Day 03 Research Agent Report")

    report_path = ARTIFACTS_DIR / "REPORT.md"
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.info("Chưa tìm thấy file `REPORT.md`.")
