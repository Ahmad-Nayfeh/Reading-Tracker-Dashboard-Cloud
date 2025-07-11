import streamlit as st

def apply_sidebar_styles():
    """
    Applies enhanced styles for the sidebar navigation links with support for both light and dark themes.
    Call this function at the beginning of each page script.
    """
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');

        /* --- Sidebar Navigation Links --- */
        [data-testid="stSidebar"] {
            direction: rtl;
        }

        /* Light theme styles */
        .light-theme [data-testid="stSidebar"] {
            background-color: #f0f2f6;
        }

        .light-theme [data-testid="stSidebarNav"] a {
            font-family: 'Inter', sans-serif;
            font-size: 1.2em !important;
            padding: 12px 15px !important;
            margin-bottom: 7px;
            border-radius: 10px;
            transition: all 0.2s ease;
            color: #4a5568;
        }

        .light-theme [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(176, 190, 197, 0.2);
            color: #2d3748;
            transform: translateX(-3px);
        }

        .light-theme [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, #9bbde0 0%, #7fa8cc 100%);
            color: white !important;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        /* Dark theme styles */
        .dark-theme [data-testid="stSidebar"] {
            background-color: #1a1a1a;
        }

        .dark-theme [data-testid="stSidebarNav"] a {
            font-family: 'Inter', sans-serif;
            font-size: 1.2em !important;
            padding: 12px 15px !important;
            margin-bottom: 7px;
            border-radius: 10px;
            transition: all 0.2s ease;
            color: #cbd5e0;
        }

        .dark-theme [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(76, 86, 106, 0.3);
            color: #e2e8f0;
            transform: translateX(-3px);
        }

        .dark-theme [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(90deg, #4a6b8a 0%, #3a5a7a 100%);
            color: white !important;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
    </style>

    <script>
        // Detect system theme preference
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

        // Apply the appropriate theme class to the body
        if (prefersDarkScheme.matches) {
            document.querySelector('body').classList.add('dark-theme');
        } else {
            document.querySelector('body').classList.add('light-theme');
        }

        // Listen for changes in theme preference
        prefersDarkScheme.addEventListener('change', e => {
            if (e.matches) {
                document.querySelector('body').classList.remove('light-theme');
                document.querySelector('body').classList.add('dark-theme');
            } else {
                document.querySelector('body').classList.remove('dark-theme');
                document.querySelector('body').classList.add('light-theme');
            }
        });
    </script>
    """, unsafe_allow_html=True)
