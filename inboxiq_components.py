"""Reusable UI fragments (task cards, etc.) for Inbox IQ pages."""

from __future__ import annotations

import html

import streamlit as st

from inboxiq_state import generate_calendar_link, normalize_people, save_task


def render_extracted_task_card(task: dict, index: int) -> None:
    """Structured NLP output card + Save + compact Calendar."""
    task_text = html.escape(str(task.get("task", "Untitled task")))
    due_date = html.escape(str(task.get("due_date") or "No due date"))
    people_label = html.escape(", ".join(normalize_people(task)) or "No person mentioned")
    priority = str(task.get("priority", "Normal"))
    safe_priority = html.escape(priority)
    priority_class = "priority-high" if priority == "High" else "priority-normal"
    priority_icon = "⚡" if priority == "High" else "○"

    main_col, cal_col = st.columns([6, 1])
    with main_col:
        st.markdown(
            f"""
            <div class="task-card">
              <div class="task-title">{task_text}</div>
              <div class="meta-row">Due · {due_date} · People · {people_label}</div>
              <div>
                <span class="pill due">{due_date}</span>
                <span class="pill people">{people_label}</span>
                <span class="pill {priority_class}">{priority_icon} {safe_priority}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Save Task", key=f"save_task_{index}", type="secondary"):
            added = save_task(task)
            st.session_state.save_feedback = "Task saved." if added else "Already in Tasks."
            st.rerun()
    with cal_col:
        st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)
        st.link_button(
            "📅",
            url=generate_calendar_link(task),
            help="Google Calendar (quick add)",
            type="tertiary",
            width="content",
            key=f"cal_extract_{index}",
        )
