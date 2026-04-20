"""
Global visual system for Inbox IQ.
"""

from __future__ import annotations

import streamlit as st

BG = "#0B0F19"
SIDEBAR_BG = "#0F172A"
SURFACE = "#111827"
ELEVATED = "#1F2937"
ACCENT = "#6366F1"
ACCENT_HOVER = "#4F46E5"
SUCCESS = "#22C55E"
TEXT_PRIMARY = "#E5E7EB"
TEXT_SECONDARY = "#9CA3AF"
TEXT_MUTED = "#6B7280"
BORDER = "#1F2937"
ERROR = "#EF4444"


def inject_global_css() -> None:
    """Inject shared CSS used across all pages."""
    st.markdown(
        f"""
        <style>
          .stApp {{
            background: {BG};
            color: {TEXT_PRIMARY};
          }}

          [data-testid="stSidebar"] {{
            background: {SIDEBAR_BG};
            border-right: 1px solid {BORDER};
          }}

          .iq-brand {{
            font-size: 1.2rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.15rem;
          }}

          .iq-brand-sub {{
            color: {TEXT_SECONDARY};
            font-size: 0.92rem;
            margin-bottom: 0.8rem;
          }}

          .iq-hero,
          .iq-section,
          .task-card,
          .warning-card {{
            background: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.85rem;
          }}

          .iq-hero-badge {{
            display: inline-block;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {ACCENT};
            margin-bottom: 0.4rem;
          }}

          .iq-hero-title {{
            margin: 0 0 0.35rem 0;
            color: {TEXT_PRIMARY};
            font-size: 2rem;
            line-height: 1.1;
          }}

          .iq-hero-sub,
          .iq-section-hint,
          .meta-row {{
            color: {TEXT_SECONDARY};
          }}

          .iq-section-head {{
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-size: 0.72rem;
            color: {TEXT_SECONDARY};
            margin-bottom: 0.25rem;
          }}

          .iq-section-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.35rem;
          }}

          .iq-page-title {{
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            color: {TEXT_PRIMARY};
          }}

          .iq-page-lead {{
            color: {TEXT_SECONDARY};
            margin-bottom: 0.7rem;
          }}

          .summary-bar {{
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0 1rem;
            font-weight: 600;
            background: {ELEVATED};
            border: 1px solid {BORDER};
            color: {TEXT_PRIMARY};
          }}

          .empty-state,
          .iq-placeholder {{
            border-radius: 12px;
            padding: 0.85rem 1rem;
            background: {SURFACE};
            border: 1px solid {BORDER};
            color: {TEXT_PRIMARY};
            margin-bottom: 0.8rem;
          }}

          .task-title {{
            font-size: 1.02rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.35rem;
          }}

          .pill {{
            display: inline-block;
            font-size: 0.77rem;
            border-radius: 999px;
            padding: 0.22rem 0.55rem;
            margin-right: 0.35rem;
            margin-top: 0.25rem;
            border: 1px solid {BORDER};
            color: {TEXT_PRIMARY};
            background: {ELEVATED};
          }}

          .pill.due,
          .pill.people,
          .pill.status {{
            background: {ELEVATED};
            border-color: {BORDER};
            color: {TEXT_PRIMARY};
          }}

          .priority-high {{
            border-color: {ERROR};
            color: #ffffff;
            background: {ERROR};
          }}

          .priority-normal {{
            border-color: {ACCENT};
            color: #ffffff;
            background: {ACCENT};
          }}

          .priority-low {{
            border-color: {TEXT_MUTED};
            color: #ffffff;
            background: {TEXT_MUTED};
          }}

          .stButton > button {{
            background: transparent;
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 10px !important;
            font-weight: 600 !important;
          }}

          .stButton > button[kind="primary"] {{
            background: {ACCENT} !important;
            color: #ffffff !important;
            border: 1px solid {ACCENT} !important;
          }}

          .stButton > button[kind="primary"]:hover {{
            background: {ACCENT_HOVER} !important;
            border-color: {ACCENT_HOVER} !important;
          }}

          .stButton > button[kind="secondary"]:hover {{
            background: {ELEVATED} !important;
            border-color: {BORDER} !important;
          }}

          .stTextArea textarea,
          .stTextInput input,
          .stDateInput input {{
            background: {SURFACE} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {BORDER} !important;
          }}

          .stTextArea textarea::placeholder,
          .stTextInput input::placeholder {{
            color: {TEXT_MUTED} !important;
          }}

          [data-testid="stSegmentedControl"] {{
            background: {SURFACE} !important;
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 0.15rem;
          }}

          [data-testid="stSegmentedControl"] button,
          [data-baseweb="segmented-control"] button {{
            color: {TEXT_SECONDARY} !important;
          }}

          [data-testid="stSegmentedControl"] button[aria-pressed="true"],
          [data-baseweb="segment"][aria-selected="true"] {{
            background: {ACCENT} !important;
            color: #ffffff !important;
            border-radius: 8px !important;
          }}

          .stRadio [role="radiogroup"] label {{
            color: {TEXT_SECONDARY} !important;
          }}

          .stMarkdown a,
          .stLinkButton a {{
            color: {ACCENT} !important;
          }}

          .warning-card {{
            border-color: {ERROR};
            color: {TEXT_PRIMARY};
          }}

          .success,
          .status-done {{
            color: {SUCCESS};
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )
