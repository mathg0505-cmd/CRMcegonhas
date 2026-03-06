from __future__ import annotations

import streamlit as st


def apply_base_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --crm-bg-1: #f4efe4;
  --crm-bg-2: #e7d3ac;
  --crm-surface: rgba(255, 255, 255, 0.72);
  --crm-ink: #1c1917;
  --crm-accent: #8a3f1e;
  --crm-border: rgba(28, 25, 23, 0.12);
}

.stApp {
  background:
    radial-gradient(circle at 0% 0%, var(--crm-bg-2) 0, transparent 32%),
    radial-gradient(circle at 100% 100%, #d6ccb8 0, transparent 36%),
    linear-gradient(160deg, var(--crm-bg-1), #f9f5ed);
  color: var(--crm-ink);
}

html, body, [class*="css"] {
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

[data-testid="stMetric"] {
  background: var(--crm-surface);
  border: 1px solid var(--crm-border);
  border-radius: 14px;
  padding: 10px 14px;
  backdrop-filter: blur(4px);
}

.stDataFrame {
  border: 1px solid var(--crm-border);
  border-radius: 12px;
  overflow: hidden;
}

.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
}

.stTabs [data-baseweb="tab"] {
  background: rgba(255, 255, 255, 0.58);
  border-radius: 10px;
  border: 1px solid var(--crm-border);
}

.stTabs [aria-selected="true"] {
  border-color: rgba(138, 63, 30, 0.45);
}

.stButton > button, .stForm button {
  border-radius: 10px;
  border: 1px solid rgba(138, 63, 30, 0.35);
}
</style>
        """,
        unsafe_allow_html=True,
    )
