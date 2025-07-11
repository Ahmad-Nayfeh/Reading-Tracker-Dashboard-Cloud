import streamlit as st

def apply_sidebar_styles():
    """
    Applies the enhanced styles for the sidebar navigation links.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Sidebar Navigation Links --- */
            [data-testid="stSidebar"] {
                direction: rtl;
            }
            
            [data-testid="stSidebarNav"] ul { 
                padding-right: 10px; 
            }
            
            [data-testid="stSidebarNav"] a {
                font-family: 'Inter', sans-serif;
                font-size: 1.1em !important; /* <--- تكبير الخط */
                padding: 10px 12px !important;
                margin-bottom: 5px;
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            
            /* --- Hover effect for sidebar links --- */
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(102, 126, 234, 0.1);
                color: #2c3e50;
                transform: translateX(-2px);
            }
            
            /* --- Style for the CURRENTLY active page link --- */
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white !important;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)
