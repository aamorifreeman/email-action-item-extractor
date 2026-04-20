"""Inbox IQ app entrypoint."""

from __future__ import annotations

import streamlit as st

from inboxiq_state import init_session_state
from inboxiq_styles import inject_global_css

st.set_page_config(
    page_title="Inbox IQ",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_global_css()

with st.sidebar:
    st.markdown('<div class="iq-brand">Inbox IQ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="iq-brand-sub">Email action-item extraction</div>',
        unsafe_allow_html=True,
    )

pages = [
    st.Page("views/extract.py", title="Extract", icon="🧠", default=True),
    st.Page("views/tasks.py", title="Tasks", icon="✅"),
    st.Page("views/integrations.py", title="Integrations", icon="🔗"),
]

st.navigation(pages).run()
