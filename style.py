import streamlit as st

CSS = """
<style>
/* hide default Streamlit chrome */
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.5rem; max-width: 1200px;}

/* sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #E8590C 0%, #FF922B 100%);
}
[data-testid="stSidebar"] * {color: #ffffff !important;}
[data-testid="stSidebar"] h1 {font-size: 1.6rem; margin-bottom: 0.5rem;}

/* metric cards */
[data-testid="stMetric"] {
    background: #ffffff;
    border-left: 6px solid #E8590C;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
[data-testid="stMetricValue"] {color: #E8590C;}

/* buttons */
.stButton > button, .stFormSubmitButton > button {
    background: #E8590C; color: #ffffff;
    border: none; border-radius: 10px;
    padding: 0.5rem 1.4rem; font-weight: 600;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #C2410C; color: #ffffff;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {gap: 8px;}
.stTabs [data-baseweb="tab"] {
    background: #FFE8D1; border-radius: 10px 10px 0 0; padding: 8px 18px;
}
.stTabs [aria-selected="true"] {background: #E8590C; color: #ffffff;}
.stTabs [aria-selected="true"] p {color: #ffffff;}

/* tables and forms */
[data-testid="stDataFrame"] {
    border-radius: 12px; overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
[data-testid="stForm"] {
    background: #ffffff; border: none; border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 1.2rem;
}

/* page banner */
.hero {
    background: linear-gradient(90deg, #E8590C, #FF922B);
    color: #ffffff; padding: 22px 28px; border-radius: 16px; margin-bottom: 1.2rem;
}
.hero h1 {margin: 0; font-size: 2rem; color: #ffffff;}
.hero p {margin: 4px 0 0 0; opacity: 0.92;}
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def banner(title, subtitle=""):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)