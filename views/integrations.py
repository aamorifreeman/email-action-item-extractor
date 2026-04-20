# Page: Integrations — Calendar quick-add, exports, future connectors
import html

import streamlit as st

from inboxiq_state import generate_bulk_calendar_link, tasks_to_csv

st.markdown('<p class="iq-page-title">Integrations</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="iq-page-lead">Connect Inbox IQ outputs to your tools. No OAuth required for Calendar quick-add—just sign in to Google in your browser when prompted.</p>',
    unsafe_allow_html=True,
)

# --- Google Calendar ---
st.markdown('<div class="iq-section">', unsafe_allow_html=True)
st.markdown('<div class="iq-section-head">Google Calendar</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-section-title">Quick-add events</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="iq-section-hint">Opens Google’s prefilled event composer. Bulk mode creates one event with every line in the description—handy for agendas.</div>',
    unsafe_allow_html=True,
)

results = st.session_state.get("results") or []
saved = st.session_state.get("saved_tasks") or []

gc1, gc2 = st.columns(2)
with gc1:
    if results:
        st.link_button(
            "Calendar: last extraction",
            url=generate_bulk_calendar_link(results),
            type="primary",
            use_container_width=True,
            help="Uses your most recent Extract results",
            key="int_cal_extract",
        )
    else:
        st.caption("Run **Extract** first to enable this link.")
with gc2:
    if saved:
        st.link_button(
            "Calendar: saved tasks",
            url=generate_bulk_calendar_link(saved),
            type="secondary",
            use_container_width=True,
            key="int_cal_saved",
        )
    else:
        st.caption("Save tasks on the **Tasks** page to enable this link.")

st.markdown("</div>", unsafe_allow_html=True)

# --- Export ---
st.markdown('<div class="iq-section">', unsafe_allow_html=True)
st.markdown('<div class="iq-section-head">Export</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-section-title">Download structured data</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="iq-section-hint">CSV includes task, due date, person, priority, and status (for saved tasks).</div>',
    unsafe_allow_html=True,
)

e1, e2 = st.columns(2)
with e1:
    st.download_button(
        "Download last extraction (CSV)",
        data=tasks_to_csv(results, include_status=False) if results else "task,due_date,person,priority\n",
        file_name="inboxiq_last_extract.csv",
        mime="text/csv",
        disabled=not results,
        use_container_width=True,
    )
with e2:
    st.download_button(
        "Download saved tasks (CSV)",
        data=tasks_to_csv(saved, include_status=True) if saved else "task,due_date,person,priority,status\n",
        file_name="inboxiq_saved_tasks.csv",
        mime="text/csv",
        disabled=not saved,
        use_container_width=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- Placeholders ---
st.markdown('<div class="iq-section">', unsafe_allow_html=True)
st.markdown('<div class="iq-section-head">Roadmap</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-section-title">Coming next</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="iq-placeholder">
      <h4>Google Tasks</h4>
      Push saved items as Tasks with due dates—planned; needs OAuth when we add it.
    </div>
    <div class="iq-placeholder">
      <h4>Notion</h4>
      Append rows to a database for team visibility—placeholder for a future API integration.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
