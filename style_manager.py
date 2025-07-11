import streamlit as st

def apply_sidebar_styles():
    """
    Applies robust styles for the sidebar that work with modern Streamlit versions
    and correctly adapt to the dark theme using the [data-theme="dark"] selector.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- General Sidebar Styles --- */
            [data-testid="stSidebar"] {
                direction: rtl;
            }
            
            [data-testid="stSidebarNav"] ul {  
                padding-right: 10px;  
            }
            
            [data-testid="stSidebarNav"] a {
                font-family: 'Inter', sans-serif;
                font-size: 1.2em !important;
                padding: 12px 15px !important;
                margin-bottom: 7px;
                border-radius: 10px;
                transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
            }
            
            [data-testid="stSidebarNav"] a:hover {
                transform: translateX(-3px);
            }

            /* --- Light Theme Styles --- */
            body[data-theme="light"] [data-testid="stSidebar"] {
                background-color: #f0f2f6;
            }
            body[data-theme="light"] [data-testid="stSidebarNav"] a {
                color: #4a5568;
            }
            body[data-theme="light"] [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(176, 190, 197, 0.2);
                color: #2d3748;
            }
            body[data-theme="light"] [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%);
                color: white !important;
                font-weight: bold;
            }

            /* --- Dark Theme Styles --- */
            body[data-theme="dark"] [data-testid="stSidebar"] {
                background-color: #0e1117; /* Matches Streamlit's default dark background */
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a {
                color: #fafafa; /* Clean white text */
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(255, 255, 255, 0.1); /* Subtle white overlay on hover */
                color: #ffffff;
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a[aria-current="page"] {
                background-color: #3b82f6; /* A vibrant blue for the active page */
                color: white !important;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)
