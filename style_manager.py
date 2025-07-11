import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar navigation links,
    adapting colors for both light and dark themes, with a larger font.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            /* --- Base styles for sidebar navigation links --- */
            [data-testid="stSidebar"] {
                direction: rtl;
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
            }
            
            /* --- Light Theme Colors (Default) --- */
            [data-testid="stSidebar"] {
                background-color: #f0f2f6; /* Very light gray for a calm background */
            }
            
            [data-testid="stSidebarNav"] a {
                color: #4a5568; /* Darker gray for text, easy on the eyes */
            }
            
            [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(176, 190, 197, 0.2); /* Soft blue-gray hover */
                color: #2d3748; /* Slightly darker text on hover */
                transform: translateX(-3px); /* More pronounced hover effect */
            }
            
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%); /* Calmer blue gradient */
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
            }

            /* --- Dark Theme Colors --- */
            body.dark [data-testid="stSidebar"] {
                background-color: #262730; /* Darker background for dark theme */
            }
            
            body.dark [data-testid="stSidebarNav"] a {
                color: #c0c0c0; /* Lighter gray for text in dark mode */
            }
            
            body.dark [data-testid="stSidebarNav"] a:hover {
                background-color: rgba(100, 149, 237, 0.15); /* Softer blue hover for dark mode */
                color: #ffffff; /* White text on hover for dark mode */
            }
            
            body.dark [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, #5c7cb5 0%, #4a6fa8 100%); /* Deeper blue gradient for dark mode */
                color: white !important;
                font-weight: bold;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Slightly more prominent shadow in dark mode */
            }
        </style>
    """, unsafe_allow_html=True)