# Page: Extract — main NLP workflow (email → structured action items)
import html

import streamlit as st

from extractor import extract_action_items, extract_action_items_gemini
from inboxiq_components import render_extracted_task_card
from inboxiq_state import (
    generate_bulk_calendar_link,
    save_all_tasks,
    tasks_to_csv,
)

DEFAULT_EMAIL = (
    "Hey team, can you send the final slides to Marcus by Friday, "
    "follow up with Jasmine next week, and review the budget before the meeting? "
    "This is important and should be done ASAP."
)

# ---- Hero: core product story ----
st.markdown(
    """
    <div class="iq-hero">
      <div class="iq-hero-badge">NLP extraction</div>
      <h1 class="iq-hero-title">INBOX IQ</h1>
      <p class="iq-hero-sub">
        Inbox IQ reads your message and surfaces tasks, deadlines, people, and urgency—built for real email threads.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Input (focal point) ----
st.markdown('<div class="iq-section">', unsafe_allow_html=True)
st.markdown('<div class="iq-section-head">Input</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-section-title">Paste your email</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="iq-section-hint">Long threads are fine—more context usually helps the model find buried tasks.</div>',
    unsafe_allow_html=True,
)

try:
    mode = st.segmented_control(
        "Extraction mode",
        ["Rule-Based NLP", "Gemini AI Extraction"],
        default="Rule-Based NLP",
    )
except Exception:
    mode = st.radio(
        "Extraction mode",
        ["Rule-Based NLP", "Gemini AI Extraction"],
        horizontal=True,
    )

sample_col, input_col = st.columns([1, 5])
with sample_col:
    st.markdown("<div style='height:2.1rem'></div>", unsafe_allow_html=True)
    use_sample = st.button("Use sample", type="secondary")
if use_sample:
    st.session_state.email_text = DEFAULT_EMAIL

with input_col:
    st.text_area(
        "Email text",
        label_visibility="collapsed",
        key="email_text",
        placeholder=(
            "Paste a full email or thread here…\n\n"
            "Example: deadlines, names, and asks buried in one message."
        ),
        height=320,
    )

if use_sample:
    st.rerun()

extract_clicked = st.button("Extract action items", type="primary", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- Run extraction before showing results ----
if extract_clicked:
    st.session_state.has_run = True
    st.session_state.gemini_error = ""
    with st.spinner("Running NLP extraction…"):
        if mode == "Rule-Based NLP":
            st.session_state.results = extract_action_items(st.session_state.email_text)
        else:
            try:
                st.session_state.results = extract_action_items_gemini(st.session_state.email_text)
            except Exception as exc:
                st.session_state.gemini_error = str(exc)
                st.session_state.results = extract_action_items(st.session_state.email_text)

# ---- Structured extraction output ----
st.markdown('<div class="iq-section">', unsafe_allow_html=True)
st.markdown('<div class="iq-section-head">Output</div>', unsafe_allow_html=True)
st.markdown('<div class="iq-section-title">Extracted action items</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="iq-section-hint">Structured fields from your email—save or export when you are ready.</div>',
    unsafe_allow_html=True,
)

if st.session_state.save_feedback:
    st.markdown(
        f"<div class='summary-bar'>💾 {html.escape(st.session_state.save_feedback)}</div>",
        unsafe_allow_html=True,
    )
    st.session_state.save_feedback = ""

if not st.session_state.has_run:
    st.markdown(
        """
        <div class="empty-state">
          <strong>Nothing extracted yet.</strong><br/>
          Paste an email above and run extraction to see detected tasks, dates, and entities.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if st.session_state.gemini_error:
        st.markdown(
            f"""
            <div class="warning-card">
              AI extraction failed — using rule-based NLP instead.<br/>
              <small>{html.escape(st.session_state.gemini_error)}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    results = st.session_state.results
    if not results:
        st.markdown(
            """
            <div class="empty-state">
              <strong>No action items detected.</strong><br/>
              Try wording with clearer asks (e.g. send, review, follow up).
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="summary-bar">✅ {len(results)} item(s) extracted from your email</div>',
            unsafe_allow_html=True,
        )

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Save all to Tasks", key="save_all_tasks_btn"):
                added, skipped = save_all_tasks(results)
                st.session_state.save_feedback = (
                    f"Saved {added} task(s); skipped {skipped} duplicate(s)."
                )
                st.rerun()
        with b2:
            st.download_button(
                "Download CSV",
                data=tasks_to_csv(results, include_status=False),
                file_name="inboxiq_extracted.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with b3:
            st.link_button(
                "Add all to Calendar",
                url=generate_bulk_calendar_link(results),
                help="One Google Calendar event listing every item in the description",
                type="secondary",
                use_container_width=True,
                key="cal_bulk_extracted",
            )

        for idx, item in enumerate(results):
            render_extracted_task_card(item, idx)

st.markdown("</div>", unsafe_allow_html=True)
