import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar navigation links with calmer colors and larger font.
    This version includes support for Streamlit's dark theme.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Base styles (Light Theme) --- */
            [data-testid="stSidebar"] {
                direction: rtl;
                background-color: #f0f2f6; /* Very light gray for a calm background */
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
                color: #4a5568; /* Darker gray for text */
            }
            
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(176, 190, 197, 0.2); /* Soft blue-gray hover */
                color: #2d3748;
                transform: translateX(-3px);
            }
            
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%); /* Calmer blue gradient */
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }

            /* --- Dark Theme Overrides --- */
            .theme-dark [data-testid="stSidebar"] {
                background-color: #1a1a2e; /* Dark navy blue for dark background */
            }

            .theme-dark [data-testid="stSidebarNav"] a {
                color: #e0e0e0; /* Light gray text for readability */
            }

            .theme-dark [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(76, 88, 114, 0.3); /* Softer, darker hover */
                color: #ffffff; /* White text on hover */
            }

            .theme-dark [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); /* Deep to vibrant blue for dark mode */
                color: white !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- مثال على كيفية الاستخدام في تطبيقك ---
# st.set_page_config(page_title="My App", layout="wide")

# apply_sidebar_styles()

# st.sidebar.page_link("app.py", label="الصفحة الرئيسية")
# st.sidebar.page_link("pages/page1.py", label="صفحة فرعية ١")
# st.sidebar.page_link("pages/page2.py", label="صفحة فرعية ٢")

# st.title("الصفحة الرئيسية")
# st.write("محتوى الصفحة هنا...")