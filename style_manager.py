import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar navigation links with calmer colors and larger font.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Sidebar Navigation Links --- */
            [data-testid="stSidebar"] {
                direction: rtl;
                background-color: #f0f2f6; /* Very light gray for a calm background */
            }
            
            [data-testid="stSidebarNav"] ul { 
                padding-right: 10px; 
            }
            
            [data-testid="stSidebarNav"] a {
                font-family: 'Inter', sans-serif;
                font-size: 1.2em !important; /* Increased font size for better readability */
                padding: 12px 15px !important; /* Slightly more padding */
                margin-bottom: 7px; /* More space between links */
                border-radius: 10px; /* Slightly more rounded corners */
                transition: all 0.2s ease;
                color: #4a5568; /* Darker gray for text, easy on the eyes */
            }
            
            /* --- Hover effect for sidebar links --- */
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(176, 190, 197, 0.2); /* Soft blue-gray hover */
                color: #2d3748; /* Slightly darker text on hover */
                transform: translateX(-3px); /* More pronounced hover effect */
            }
            
            /* --- Style for the CURRENTLY active page link --- */
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%); /* Calmer blue gradient */
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
            }
        </style>
    """, unsafe_allow_html=True)