"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py
Public link (team showdown):
    cloudflared tunnel --url http://localhost:8501

Reuses the exact tool loop from chat.py, and writes transcripts/*.transcript.json
in the same format, so UI sessions count as live-chat evidence.
Owner of polishing: doanlong9304.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

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

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini", "ollama"]

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")

# ---------------- Sidebar config ----------------
with st.sidebar:
    st.header("⚙️ Config")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    model = st.text_input("Model (trống = default của provider)", value="") or None
    version = st.text_input("Version label", value="v3")
    prompt_path = Path(st.text_input("System prompt", value=str(ARTIFACTS_DIR / "system_prompt.md")))
    tools_path = Path(st.text_input("Tools yaml", value=str(ARTIFACTS_DIR / "tools.yaml")))
    max_rounds = st.slider("Max tool rounds", 1, 8, 4)
    history_window = st.slider("History window (pairs)", 0, 10, 5)
    show_tools = st.checkbox("Hiện chi tiết tool calls", value=True)
    if st.button("🗑️ New chat"):
        for key in ("messages", "history", "transcript", "transcript_path"):
            st.session_state.pop(key, None)
        st.rerun()


@st.cache_resource(show_spinner=False)
def get_provider(name: str) -> Any:
    return make_provider(name)


def new_transcript() -> tuple[dict[str, Any], Path]:
    artifact_version = build_artifact_version(version, prompt_path, tools_path)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = "_".join([safe_slug(version), safe_slug(provider_name), "ui", stamp])
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


st.session_state.setdefault("messages", [])   # what the UI shows
st.session_state.setdefault("history", [])    # what the model sees (user/assistant pairs)
if "transcript" not in st.session_state:
    st.session_state.transcript, st.session_state.transcript_path = new_transcript()

st.title("🔎 Research Agent")
st.caption(f"provider=`{provider_name}` · version=`{version}` · transcript=`{st.session_state.transcript_path.name}`")


def render_tool_events(rounds: list[dict[str, Any]]) -> None:
    for rnd in rounds:
        for event in rnd.get("tool_results", []):
            label = f"🔧 round {rnd['round']} · {event['tool']}({json.dumps(event['args'], ensure_ascii=False)})"
            with st.expander(label):
                st.json(event.get("result", {}))


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if show_tools and msg.get("rounds"):
            render_tool_events(msg["rounds"])
        st.markdown(msg["content"])

user_text = st.chat_input("Hỏi agent… (vd: Tin AI mới nhất tuần này?)")
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
        with st.spinner("Agent đang chạy tool…"):
            try:
                result = run_model_tool_loop(
                    provider=get_provider(provider_name),
                    messages=messages,
                    tools=tools,
                    model=model,
                    max_tool_rounds=max_rounds,
                )
                answer = result["assistant_text"] or "(không có câu trả lời)"
                turn.update(result)
            except Exception as exc:  # show provider errors instead of crashing the page
                result = {"rounds": []}
                answer = f"❌ {type(exc).__name__}: {exc}"
                turn.update({"status": "provider_error", "error": answer})
        if show_tools:
            render_tool_events(result.get("rounds", []))
        if result.get("status") == "waiting_for_user":
            st.info("Agent đang hỏi lại bạn — trả lời ở ô chat bên dưới.")
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
