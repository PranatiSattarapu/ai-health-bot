

# import streamlit as st
# from drive_manager import list_data_files
# from workflow import generate_response

# # --- Streamlit Configuration ---
# st.set_page_config(page_title="Health Tutor Console", layout="wide")
# st.title("Prompt Refinement Console")

# # --- Initialize Session State ---
# if "sessions" not in st.session_state:
#     st.session_state.sessions = {"Session 1": []}
# if "current_session" not in st.session_state:
#     st.session_state.current_session = "Session 1"

# # --- Sidebar: Document Management (Read-Only) ---
# st.sidebar.header("📂 Current Document Context")

# files = list_data_files()

# if not files:
#     st.sidebar.info("No documents found in the shared folder yet.")
# else:
#     st.sidebar.markdown("**Documents informing the context:**")
#     for f in files:
#         st.sidebar.markdown(f"📄 " + f["name"])

# st.divider()

# # --- Main Area: Chat Interface ---
# # --- Main Chat Interface ---

# active_messages = st.session_state.sessions[st.session_state.current_session]

# # 1️⃣ CHAT MESSAGES (always on top)
# for message in active_messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])


# # 2️⃣ QUICK QUESTIONS (always ABOVE chat input)
# st.markdown("### Quick Questions")

# preset_questions = [
#     "Summarize health status over the last 30 days",
#     "What's my health summary?",
#     "What should I ask my doctor?",
#     "Summarize my recent metrics",
# ]

# cols = st.columns(len(preset_questions))

# if "preset_query" not in st.session_state:
#     st.session_state.preset_query = None

# for i, q in enumerate(preset_questions):
#     if cols[i].button(q, key=f"preset_{i}"):
#         st.session_state.preset_query = q
#         st.rerun()


# # 3️⃣ CHAT INPUT (always at the bottom)
# chat_input = st.chat_input("Enter your medical question:")

# # Decide final query
# query = None
# if st.session_state.preset_query:
#     query = st.session_state.preset_query
#     st.session_state.preset_query = None
# elif chat_input:
#     query = chat_input


# # 4️⃣ PROCESS QUERY
# if query:
#     active_messages.append({"role": "user", "content": query})

#     with st.chat_message("user"):
#         st.markdown(query)

#     with st.chat_message("assistant"):
#         with st.spinner("Claude is thinking..."):
#             answer = generate_response(query)

#         st.markdown(answer)

#     active_messages.append({"role": "assistant", "content": answer})
#     st.session_state.sessions[st.session_state.current_session] = active_messages


import streamlit as st
from workflow import generate_response
from datetime import datetime

# --- Streamlit Configuration ---
st.set_page_config(page_title="Health Tutor Console", layout="wide")

# --- Custom CSS ---
# Add Bootstrap Icons CDN
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
""", unsafe_allow_html=True)

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
    
    .preset-icon i {
        display: flex;
        align-items: center;
        justify-content: center;
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
    
    /* Right panel styling */
    .right-panel {
        position: fixed;
        top: 0px; 
        right: 0px;
        width: 25vw;
        background: #dceaf7;
        padding: 2rem 1.5rem;
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
        text-align: start;
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

    .right-panel .alert-icon i {
        font-size: 2rem;
        color: #1E1E1E;
    }

    .right-panel .alert-count {
        font-size: 2rem;
        color: red !important;
        font-weight: normal;
    }

    .right-panel .action-icon {
        font-size: 2rem;
        flex-shrink: 0;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .right-panel .action-icon i {
        font-size: 2rem;
        color: #1E1E1E;
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

# --- Initialize Session State ---
if "sessions" not in st.session_state:
    st.session_state.sessions = {"Session 1": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "Session 1"
if "preset_query" not in st.session_state:
    st.session_state.preset_query = None
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

# --- Sidebar: Chat History ---
with st.sidebar:
    st.markdown("""
      <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
        <i class="bi bi-chat-dots" style="font-size: 1.5rem; color: #1E1E1E; flex-shrink: 0;"></i>
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

# --- Main Layout: Chat + Right Panel ---
main_col, right_col = st.columns([8, 2])

with main_col:
    # Greeting + Date
    today = datetime.now().strftime("%B %d, %Y")
    st.markdown(
        f"""
        <div style='text-align: left; margin-bottom: 3rem;'>
            <h2 style='color: black; margin-bottom: 5px; font-size: 2.5rem;'>Hello!</h2>
            <p style='font-size: 1.25rem; color: gray;'>{today}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display chat messages
    active_messages = st.session_state.sessions[st.session_state.current_session]

    for message in active_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Preset questions
    preset_questions = [
        {
            "icon": """<div class="preset-icon">
                <i class="bi bi-calendar-check" style="font-size: 2.25rem; color: #1E1E1E;"></i>
            </div>""",
            "text": "Summarize health status over the last 30 days"
        },
        {
            "icon": """<div class="preset-icon">
                <i class="bi bi-hospital" style="font-size: 2.25rem; color: #1E1E1E;"></i>
            </div>""",
            "text": "Help me prepare for my Care Provider visit"
        },
        {
            "icon": """<div class="preset-icon">
                <i class="bi bi-heart-pulse" style="font-size: 2.25rem; color: #1E1E1E;"></i>
            </div>""",
            "text": "Give me my heart health status"
        },
        {
            "icon": """<div class="preset-icon">
                <i class="bi bi-exclamation-triangle" style="font-size: 2.25rem; color: #1E1E1E;"></i>
            </div>""",
            "text": "Explain my alerts"
        },
    ]

    # Display preset buttons
    left_col = st.container()

    with left_col:
        for i, q in enumerate(preset_questions):
            btn_col1, btn_col2 = st.columns([0.05, 0.95])
            with btn_col1:
                st.markdown(f'<div style="display: flex; align-items: start; justify-content: start; height: 100%;">{q["icon"]}</div>', unsafe_allow_html=True)
            with btn_col2:
                if st.button(q["text"], key=f"preset_{i}", use_container_width=True):
                    st.session_state.preset_query = q["text"]
                    st.rerun()

    # Process query
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
            with st.spinner("Thinking..."):
                answer = generate_response(query)

            st.markdown(answer)

        active_messages.append({"role": "assistant", "content": answer})
        st.session_state.sessions[st.session_state.current_session] = active_messages

# Right panel HTML (fixed position)
st.markdown("""
<div class="right-panel">
    <div class="alert-section">
        <div class="alert-icon" style="position: relative;">
            <i class="bi bi-bell-fill" style="font-size: 2rem; color: #1E1E1E;"></i>
        </div>
        <div class="alert-count">2 Alerts</div>
    </div>
    <div class="action-item">
        <div class="action-icon">
            <i class="bi bi-share" style="font-size: 2rem; color: #1E1E1E;"></i>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Share with Carepod</span>
    </div>
   <div class="action-item">
        <div class="action-icon">
            <i class="bi bi-camera" style="font-size: 2rem; color: #1E1E1E;"></i>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">Add Health Photos</span>
    </div>
   <div class="action-item">
        <div class="action-icon">
            <i class="bi bi-graph-up" style="font-size: 2rem; color: #1E1E1E;"></i>
        </div>
        <span style="font-size: 1.5rem; color: #1E1E1E; font-weight: normal; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">View Dashboard</span>
    </div>
</div>
""", unsafe_allow_html=True)
