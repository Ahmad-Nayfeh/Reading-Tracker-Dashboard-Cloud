import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar navigation links with calmer colors and larger font,
    supporting both light and dark themes using CSS variables.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
            
            :root {
                /* --- Light Theme Variables --- */
                --sidebar-bg-color: #f0f2f6; /* Very light gray for a calm background */
                --link-text-color: #4a5568; /* Darker gray for text, easy on the eyes */
                --link-hover-bg: rgba(176, 190, 197, 0.2); /* Soft blue-gray hover */
                --link-hover-text: #2d3748; /* Slightly darker text on hover */
                --active-link-gradient-start: #9bbde0; /* Calmer blue gradient start */
                --active-link-gradient-end: #7fa8cc; /* Calmer blue gradient end */
                --active-link-text-color: white;
                --active-link-shadow: rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
            }

            @media (prefers-color-scheme: dark) {
                /* --- Dark Theme Variables --- */
                :root {
                    --sidebar-bg-color: #1a1a2e; /* Darker background for sidebar */
                    --link-text-color: #e0e0e0; /* Lighter text for dark theme */
                    --link-hover-bg: rgba(60, 60, 80, 0.4); /* Darker hover effect */
                    --link-hover-text: #ffffff; /* White text on hover */
                    --active-link-gradient-start: #5b6b90; /* Darker blue gradient start */
                    --active-link-gradient-end: #3a4a6e; /* Darker blue gradient end */
                    --active-link-text-color: #ffffff;
                    --active-link-shadow: rgba(0, 0, 0, 0.3); /* More pronounced shadow */
                }
            }
            
            /* --- Sidebar Navigation Links General Styles --- */
            [data-testid="stSidebar"] {
                direction: rtl;
                background-color: var(--sidebar-bg-color); /* Use variable */
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
                color: var(--link-text-color); /* Use variable */
            }
            
            /* --- Hover effect for sidebar links --- */
            [data-testid="stSidebarNav"] a:hover {
                background-color: var(--link-hover-bg); /* Use variable */
                color: var(--link-hover-text); /* Use variable */
                transform: translateX(-3px); /* More pronounced hover effect */
            }
            
            /* --- Style for the CURRENTLY active page link --- */
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background: linear-gradient(90deg, var(--active-link-gradient-start) 0%, var(--active-link-gradient-end) 100%); /* Use variables */
                color: var(--active-link-text-color) !important; /* Use variable */
                font-weight: bold;
                box-shadow: 0 4px 8px var(--active-link-shadow); /* Use variable */
            }
        </style>
    """, unsafe_allow_html=True)

