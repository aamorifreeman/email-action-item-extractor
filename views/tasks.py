# Page: Tasks — session-saved items from extraction (secondary to Extract)
import html

import streamlit as st

from inboxiq_state import (
    delete_task,
    generate_bulk_calendar_link,
    generate_calendar_link,
    normalize_people,
    tasks_to_csv,
    toggle_task_status,
)

st.markdown('<p class="iq-page-title">Saved tasks</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="iq-page-lead">Items you saved from <strong>Extract</strong> for this session—lightweight follow-up, not a full task manager.</p>',
    unsafe_allow_html=True,
)

saved = st.session_state.saved_tasks

if not saved:
    st.markdown(
        """
        <div class="empty-state">
          <strong>No saved tasks yet.</strong><br/>
          Go to <strong>Extract</strong>, run NLP on an email, then use <em>Save Task</em> or <em>Save all to Tasks</em>.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="summary-bar">📌 {len(saved)} task(s) saved this session</div>',
        unsafe_allow_html=True,
    )

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Export CSV",
            data=tasks_to_csv(saved, include_status=True),
            file_name="inboxiq_tasks.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.link_button(
            "Add all to Calendar",
            url=generate_bulk_calendar_link(saved),
            type="secondary",
            use_container_width=True,
            key="cal_bulk_saved_page",
        )

    for task in saved:
        tid = task["id"]
        task_text = html.escape(str(task.get("task", "Untitled task")))
        due_date = html.escape(str(task.get("due_date") or "—"))
        people_label = html.escape(", ".join(normalize_people(task)) or "—")
        priority = str(task.get("priority", "Normal"))
        status = str(task.get("status", "To Do"))
        priority_class = "priority-high" if priority == "High" else "priority-normal"
        status_icon = "✓" if status == "Done" else "○"

        row_main, row_cal = st.columns([6, 1])
        with row_main:
            st.markdown(
                f"""
                <div class="task-card">
                  <div class="task-title">{task_text}</div>
                  <div class="meta-row">Due · {due_date} · {people_label}</div>
                  <div>
                    <span class="pill due">{due_date}</span>
                    <span class="pill people">{people_label}</span>
                    <span class="pill {priority_class}">{html.escape(priority)}</span>
                    <span class="pill status">{status_icon} {html.escape(status)}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with row_cal:
            st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
            st.link_button(
                "📅",
                url=generate_calendar_link(task),
                type="tertiary",
                width="content",
                key=f"cal_saved_{tid}",
            )

        c1, c2 = st.columns(2)
        with c1:
            toggle_label = "Mark active" if status == "Done" else "Mark done"
            if st.button(toggle_label, key=f"toggle_{tid}", type="secondary"):
                toggle_task_status(tid)
                st.rerun()
        with c2:
            if st.button("Delete", key=f"delete_{tid}", type="secondary"):
                delete_task(tid)
                st.rerun()
