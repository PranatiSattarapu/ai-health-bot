import streamlit as st
from drive_manager import list_data_files
from workflow import generate_response
from datetime import datetime

# --- IMPORTANT: Initialize cache keys BEFORE importing code uses them ---
CACHE_KEYS = [
    "cached_guidelines",
    "cached_frameworks",
    "cached_patient_files",
    "cached_guideline_contents"
]

for key in CACHE_KEYS:
    if key not in st.session_state:
        st.session_state[key] = None


# --- Streamlit Configuration ---
st.set_page_config(page_title="Health Tutor Console", layout="wide")

# --- Custom CSS for Right Panel ---
# --- Custom CSS (merged theme) ---
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom styling */
    .stApp {
        background-color: white;
    }
    
    [data-testid="stSidebar"] {
        background-color: #EFEFEF;
        width: 20vw;
        min-width: 20vw;
    }
    
    [data-testid="stSidebar"][aria-expanded="true"] {
        width: 20vw;
        min-width: 20vw;
    }

    .stMain {
        padding-right: 20vw;
    }
    
    .stMainBlockContainer {
        padding:1.5rem 3rem ;
        margin:0;        
    }
    
    .main-container {
        background-color: white;
        padding: 2rem 3rem;
        border-radius: 10px;
        margin: 1rem;
        margin-right: 20vw;
    }
    
    .greeting-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E1E1E;
        margin-bottom: 0.3rem;
    }
    
    .date-display {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .action-button {
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        font-size: 1.05rem;
        width: 100%;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
        color: #1E1E1E;
    }
    
    .action-button:hover {
        border-color: #4A90E2;
        box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
    }
    
    .stButton > button {
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 10px;
        padding: 2rem 1rem;
        font-size: 1.05rem;
        width: 100%;
        color: #1E1E1E;
        transition: all 0.2s;
        display: flex;
        align-items: center;
    }
    
    .stButton > button {
        background: white;
        border: 2px solid #E0E0E0;
        border-radius: 10px;
        padding: 1.5rem 1rem;
        font-size: 1.05rem;
        width: 100%;
        color: #1E1E1E;
        transition: all 0.2s;
        display: flex;
        align-items: center;
    }
    
    .preset-icon {
        flex-shrink: 0;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .preset-icon svg {
        width: 36px;
        height: 36px;
    }
    
    .alert-box {
        background-color: #E3F2FD;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sidebar-section {
        margin-bottom: 2rem;
    }
    
    .chat-message {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .right-sidebar {
        background-color: #dceaf7;
        padding: 2rem 1.5rem;
        border-radius: 10px;
        min-height: 100vh;
    }

    .stAppHeader {
    display: none;
    }
    
    /* Apply background to the entire right column container */
    .element-container:has(.right-sidebar) {
        background-color: #dceaf7 !important;
    }
    .stHorizontalBlock {
            align-items:center;
            justify-content:between;
    }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Force all normal text in the main content to be black */
div[data-testid="stVerticalBlock"] * {
    color: #1E1E1E !important;
}

/* Fix gray text inside preset buttons */
.stButton > button {
    color: #1E1E1E !important;
}

/* Fix chat bubbles text */
.stChatMessageContent p, .stChatMessageContent div {
    color: #1E1E1E !important;
}
</style>
""", unsafe_allow_html=True)



# st.title("Prompt Refinement Console")

# --- Initialize Session State ---
if "sessions" not in st.session_state:
    st.session_state.sessions = {"Session 1": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "Session 1"
if "preset_query" not in st.session_state:
    st.session_state.preset_query = None
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False


# --- Sidebar: Document Management (Read-Only) ---
# st.sidebar.header("📂 Current Document Context")
# if st.sidebar.button("🔍 Test Patient Data API"):
#     from workflow import fetch_patient_data
#     data = fetch_patient_data()
#     st.sidebar.write("API Returned:")
#     st.sidebar.json(data)

# files = list_data_files()

# if not files:
#     st.sidebar.info("No documents found in the shared folder yet.")
# else:
#     st.sidebar.markdown("**Documents informing the context:**")
#     for f in files:
#         st.sidebar.markdown(f"📄 " + f["name"])
with st.sidebar:
    st.markdown("""
      <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0;">
            <path d="M4 4h16c1.1 0 2 .9 2 2v8c0 1.1-.9 2-2 2h-6l-4 4-4-4H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="8" cy="10" r="1" fill="#1E1E1E"/>
            <circle cx="12" cy="10" r="1" fill="#1E1E1E"/>
            <circle cx="16" cy="10" r="1" fill="#1E1E1E"/>
            <path d="M6 18l-2 2v-2" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <h3 style="font-size: 1.5rem; font-weight: 600; color: #1E1E1E; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Chat History</h3>
    </div>
    <div class="chat-history" style="margin-top: 1rem;">
        <ul style="list-style: none; padding: 0; margin: 0;">
            <li style="padding: 0.75rem; margin-bottom: 0.5rem; background-color: #F5F5F5; border-radius: 8px; cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#E8E8E8'" onmouseout="this.style.backgroundColor='#F5F5F5'">
                <span style="font-size: 0.9rem; color: #1E1E1E; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Give me my 30-day health report</span>
            </li>
            <li style="padding: 0.75rem; margin-bottom: 0.5rem; background-color: #F5F5F5; border-radius: 8px; cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#E8E8E8'" onmouseout="this.style.backgroundColor='#F5F5F5'">
                <span style="font-size: 0.9rem; color: #1E1E1E; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Help me prepare for my Care Provider visit</span>
            </li>
            <li style="padding: 0.75rem; margin-bottom: 0.5rem; background-color: #F5F5F5; border-radius: 8px; cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#E8E8E8'" onmouseout="this.style.backgroundColor='#F5F5F5'">
                <span style="font-size: 0.9rem; color: #1E1E1E; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Give me my heart health status</span>
            </li>
            <li style="padding: 0.75rem; margin-bottom: 0.5rem; background-color: #F5F5F5; border-radius: 8px; cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#E8E8E8'" onmouseout="this.style.backgroundColor='#F5F5F5'">
                <span style="font-size: 0.9rem; color: #1E1E1E; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Explain my alerts</span>
            </li>
            <li style="padding: 0.75rem; margin-bottom: 0.5rem; background-color: #F5F5F5; border-radius: 8px; cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#E8E8E8'" onmouseout="this.style.backgroundColor='#F5F5F5'">
                <span style="font-size: 0.9rem; color: #1E1E1E; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">What are my recent symptoms?</span>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# st.divider()

# --- Main Layout: Chat + Right Panel ---
# Greeting + Date

main_col, right_col = st.columns([8, 2])

with main_col:

    # Greeting + Date (THIS GOES HERE)
    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(
    f"""
    <div style='text-align: left; margin-bottom: 3rem;'>
        <h2 style='color: black; margin-bottom: 5px; font-size: 2.5rem;'>Helslo!</h2>
        <p style='font-size: 1.25rem; color: gray;'>{today}</p>
    </div>
    """,
    unsafe_allow_html=True
)



    active_messages = st.session_state.sessions[st.session_state.current_session]

    for message in active_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    preset_questions = [
        {
            "icon": """<div class="preset-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="4" width="18" height="18" rx="2" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M3 10h18M8 2v4M16 2v4" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round"/>
                    <rect x="7" y="14" width="2" height="2" rx="0.5" fill="#1E1E1E"/>
                    <rect x="11" y="14" width="2" height="2" rx="0.5" fill="#1E1E1E"/>
                    <rect x="15" y="14" width="2" height="2" rx="0.5" fill="#1E1E1E"/>
                </svg>
            </div>""",
            "text": "Give me my 30-day health report"
        },
        {
            "icon": """<div class="preset-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 12a3 3 0 1 0 6 0 3 3 0 0 0-6 0z" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M12 12v7M12 5v3" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round"/>
                    <path d="M8 12a4 4 0 0 1 8 0" stroke="#1E1E1E" stroke-width="1" fill="none" stroke-linecap="round"/>
                    <circle cx="6.5" cy="19" r="2" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <circle cx="17.5" cy="19" r="2" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M6.5 19h11" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round"/>
                </svg>
            </div>""",
            "text": "Help me prepare for my Care Provider visit"
        },
        {
            "icon": """<div class="preset-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="10" cy="10" r="7" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M16 16l3 3" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M5 10h1.5M7 7.5h1.5M9.5 6h1M12 7.5h1M14.5 10h1M10 10h1M8 12h1M10 13.5h1M12 12h1M14 12h1" stroke="#1E1E1E" stroke-width="1.5" stroke-linecap="round"/>
                    <path d="M5 10l2.5-2.5 2 2.5 2-2.5 2.5 2.5" stroke="#1E1E1E" stroke-width="1" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>""",
            "text": "Give me my heart health status"
        },
        {
            "icon": """<div class="preset-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="7" cy="7" r="2.5" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M7 9.5v2.5M7 12c-1.5 0-2.5 1-2.5 2.5" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M7 9.5l3 2.5" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
                    <rect x="13" y="5" width="8" height="10" rx="1" stroke="#1E1E1E" stroke-width="1" fill="none"/>
                    <path d="M15 8h4M15 10h4M15 12h2" stroke="#1E1E1E" stroke-width="1" stroke-linecap="round"/>
                </svg>
            </div>""",
            "text": "Explain my alerts"
        },
    ]
    if "preset_query" not in st.session_state:
        st.session_state.preset_query = None

    # Center the buttons using columns
    left_col = st.container()

    with left_col:
        for i, q in enumerate(preset_questions):
            # Use columns to create a button-like layout with SVG
            btn_col1, btn_col2 = st.columns([0.05, 0.95])
            with btn_col1:
                st.markdown(f'<div style="display: flex; align-items: start; justify-content: start; height: 100%;">{q["icon"]}</div>', unsafe_allow_html=True)
            with btn_col2:
                if st.button(q["text"], key=f"preset_{i}", use_container_width=True):
                    st.session_state.preset_query = q["text"]
                    st.rerun()


    # Decide final query
    query = None
    if st.session_state.preset_query:
        query = st.session_state.preset_query
        st.session_state.preset_query = None

    # PROCESS QUERY
    if query:
        active_messages.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Claude is thinking..."):
                answer = generate_response(query)

            st.markdown(answer)

        active_messages.append({"role": "assistant", "content": answer})
        st.session_state.sessions[st.session_state.current_session] = active_messages

# Right panel CSS (shown on all screens)
st.markdown("""
<style>
.right-panel {
    position: fixed;
    top: 0px; 
    right: 0px;
    width: 25vw;
    background: #dceaf7;
    padding: 2rem 1.5rem;
    # box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
    # z-index: 999;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.right-panel .alert-section {
    background-color: #dceaf7;
    padding: 2rem;
    border-radius: 10px;
    text-align: satrt;
    margin-bottom: 3rem;
    width: 100%;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: start;
    gap: 1rem;
}

.right-panel .alert-icon {
    font-size: 3rem;
    margin-bottom: 0;
    display: flex;
    justify-content: center;
    align-items: center;
}

.right-panel .alert-icon svg {
    width: 32px;
    height: 32px;
}

.right-panel .alert-count {
    font-size: 2rem;
    color: #E4080A !important;
    font-weight: normal;
}

.right-panel .action-icon {
    font-size: 2rem;
    flex-shrink: 0;
    display: flex;
    justify-content: center;
    align-items: center;
}

.right-panel .action-icon svg {
    width: 32px;
    height: 32px;
}
.right-panel .action-icon svg {
    width: 32px;
    height: 32px;
}

.right-panel .action-item {
    background-color: #dceaf7;
    padding: 2rem;
    border-radius: 10px;
    text-align: left;
    width: 100%;
    display: flex;
    flex-direction: row;
    align-items: start;
    justify-content: start;
    gap: 1rem;
}
</style>
""", unsafe_allow_html=True)
# Right panel HTML (shown on all screens)
st.markdown("""
<div class="right-panel">
    <div class="alert-section">
        <div class="alert-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="18" cy="8" r="1" fill="#E74C3C"/>
            </svg>
        </div>
        <div class="alert-count">2 Alerts</div>
    </div>
    <div class="action-item">
        <div class="action-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="16 6 12 2 8 6" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="2" x2="12" y2="15" stroke="#1E1E1E" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Share with Carepod</span>
    </div>
   <div class="action-item">
        <div class="action-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="#1E1E1E" stroke-width="1.5" fill="none"/>
                <path d="M12 8v8M8 12h8" stroke="#1E1E1E" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Add Health Photos</span>
    </div>
   <div class="action-item">
        <div class="action-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 3v18h18" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 12l4-4 4 4 6-6" stroke="#1E1E1E" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="7" y="16" width="2" height="2" fill="#1E1E1E"/>
                <rect x="11" y="14" width="2" height="4" fill="#1E1E1E"/>
                <rect x="15" y="10" width="2" height="8" fill="#1E1E1E"/>
            </svg>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">View Dashboard</span>
    </div>
</div>
""", unsafe_allow_html=True)