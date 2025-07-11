import streamlit as st

def apply_sidebar_styles():
    """
    Applies the enhanced, calm styles for the sidebar navigation links.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Sidebar Container RTL --- */
            [data-testid="stSidebar"] {
                direction: rtl;
                background-color: #f4f7f6; /* Soft mint-green background */
            }
            
            /* --- Navigation List Spacing --- */
            [data-testid="stSidebarNav"] ul {
                padding-right: 12px;
            }
            
            /* --- Link Base Styles --- */
            [data-testid="stSidebarNav"] a {
                font-family: 'Inter', sans-serif;
                font-size: 1.3em !important; /* تكبير الخط */
                padding: 12px 14px !important;
                margin-bottom: 6px;
                border-radius: 10px;
                color: #2f4f4f; /* Dark slate color */
                transition: all 0.3s ease;
            }
            
            /* --- Hover Effect --- */
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(183, 215, 207, 0.4); /* Muted teal hover */
                color: #1b262c;
                transform: translateX(-2px);
            }
            
            /* --- Active Page Link --- */
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #a8dadc 0%, #457b9d 100%); /* Calm blue gradient */
                color: #ffffff !important;
                font-weight: 600;
            }
        </style>
    """, unsafe_allow_html=True)
