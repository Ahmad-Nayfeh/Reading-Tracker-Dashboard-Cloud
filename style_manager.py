import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar and main content,
    adapting colors for both light and dark themes.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Sidebar Styles (already provided) --- */
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
                transition: all 0.2s ease;
            }
            
            /* --- Light Theme Colors for Sidebar --- */
            [data-testid="stSidebar"] {
                background-color: #f0f2f6;
            }
            
            [data-testid="stSidebarNav"] a {
                color: #4a5568;
            }
            
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(176, 190, 197, 0.2);
                color: #2d3748;
                transform: translateX(-3px);
            }
            
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%);
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }

            /* --- Dark Theme Colors for Sidebar --- */
            body.dark [data-testid="stSidebar"] {
                background-color: #262730;
            }
            
            body.dark [data-testid="stSidebarNav"] a {
                color: #c0c0c0;
            }
            
            body.dark [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(100, 149, 237, 0.15);
                color: #ffffff;
            }
            
            body.dark [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #5c7cb5 0%, #4a6fa8 100%);
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }

            /* --- NEW: Force Black Text for specific elements on Light Backgrounds --- */
            /* This targets any light-colored container to make sure its text is readable */
            .st-emotion-cache-1r70h2u, .st-emotion-cache-16j0g5o {
                color: #000000 !important; /* Force black text */
            }
            
        </style>
    """, unsafe_allow_html=True)