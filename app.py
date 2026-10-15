import streamlit as st


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

# app.py is the entry point. Pages are listed explicitly so they
# work the same locally and on Streamlit Community Cloud.

pages = [
    st.Page(
        "home.py",
        title="Report Generator",
        icon="⛸️",
        default=True
    ),
    st.Page(
        "pages/About.py",
        title="About",
        icon="ℹ️"
    )
]

st.navigation(pages).run()
