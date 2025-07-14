import streamlit as st

def apply_sidebar_styles():
    """
    Applies robust styles for the sidebar with larger fonts.
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
            
            /* --- Sidebar Link Font Size Increase --- */
            [data-testid="stSidebarNav"] a {
                font-family: 'Inter', sans-serif;
                font-size: 2.5em !important; /* زيادة كبيرة في حجم خط الشريط الجانبي */
                padding: 14px 18px !important; /* تعديل الحشو ليتناسب مع الخط الكبير */
                margin-bottom: 8px;
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
                background-color: #0e1117; 
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a {
                color: #fafafa;
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            body[data-theme="dark"] [data-testid="stSidebarNav"] a[aria-current="page"] {
                background-color: #3b82f6;
                color: white !important;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)