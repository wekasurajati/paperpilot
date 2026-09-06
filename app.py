import base64
import os
import tempfile

import streamlit as st
from rag_engine import PaperPilotSession

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_ICON_PATH = os.path.join(ASSETS_DIR, "paperpilotlogo.png")     # used everywhere: favicon, avatar, hero, sidebar
LOGO_WORDMARK_PATH = LOGO_ICON_PATH

st.set_page_config(page_title="PaperPilot", page_icon=LOGO_ICON_PATH, layout="wide")


def _img_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


ICON_B64 = _img_base64(LOGO_ICON_PATH)
WORDMARK_B64 = _img_base64(LOGO_WORDMARK_PATH)

# Simple line-art person icon as a data URI, used as the user's chat avatar
# so it visually matches the assistant's logo avatar instead of Streamlit's
# default red placeholder circle.
USER_AVATAR = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" height="40">'
        b'<circle cx="12" cy="8" r="4" fill="none" stroke="#9570FA" stroke-width="1.8"/>'
        b'<path d="M4 20c1.6-4.2 4.6-6.3 8-6.3s6.4 2.1 8 6.3" fill="none" '
        b'stroke="#9570FA" stroke-width="1.8" stroke-linecap="round"/>'
        b"</svg>"
    ).decode()
)

# ============================================================
# Inline SVG icon set (stroke-based, no emoji anywhere)
# ============================================================
ICONS = {
    "upload": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3"/></svg>',
    "sliders": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
    "file": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "link": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "compass": '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>',
    "refresh": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
}


def icon(name: str) -> str:
    return f'<span class="pp-icon">{ICONS[name]}</span>'


# ============================================================
# GLOBAL STYLE
# ============================================================
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

    :root {{
        --accent: #9570FA;
        --accent-strong: #6C4FE0;
        --text-color: #1D1B2E;
        --text-muted: #6A6483;
        --glass-bg: rgba(255, 255, 255, 0.62);
        --glass-border: rgba(255, 255, 255, 0.8);
        --glass-shadow: rgba(90, 70, 180, 0.12);
        --page-bg: #F6F5FA;
        --blob-a: rgba(149, 112, 250, 0.30);
        --blob-b: rgba(108, 79, 224, 0.22);
        --blob-c: rgba(180, 160, 255, 0.28);
        --input-bg: rgba(255, 255, 255, 0.85);
    }}

    @media (prefers-color-scheme: dark) {{
        :root {{
            --accent: #B39DFB;
            --accent-strong: #9570FA;
            --text-color: #EDEBFF;
            --text-muted: #A79FCB;
            --glass-bg: rgba(28, 24, 46, 0.55);
            --glass-border: rgba(255, 255, 255, 0.10);
            --glass-shadow: rgba(0, 0, 0, 0.45);
            --page-bg: #131217;
            --blob-a: rgba(149, 112, 250, 0.28);
            --blob-b: rgba(80, 60, 170, 0.30);
            --blob-c: rgba(60, 45, 120, 0.35);
            --input-bg: rgba(255, 255, 255, 0.06);
        }}
    }}

    html, body {{
        background: var(--page-bg);
    }}

    /* Icon-font safety net: never let the Montserrat override break Streamlit's
       own material-icon glyphs (this is what caused "keyboard_double_arrow..."
       to show up as literal text instead of an arrow icon). */
    [data-testid="stIconMaterial"],
    span[class*="material-symbols"],
    span.material-icons {{
        font-family: 'Material Symbols Outlined', 'Material Symbols Rounded', 'Material Icons' !important;
    }}

    .stApp {{
        font-family: 'Montserrat', sans-serif;
        color: var(--text-color);
        background: transparent;
    }}
    .stApp p, .stApp span, .stApp label, .stApp div, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp textarea, .stApp input {{
        font-family: 'Montserrat', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* ---------- Gemini-style aurora background ---------- */
    .pp-aurora {{
        position: fixed;
        inset: 0;
        z-index: -1;
        overflow: hidden;
        background: var(--page-bg);
    }}
    .pp-aurora span {{
        position: absolute;
        border-radius: 50%;
        filter: blur(90px);
    }}
    .pp-aurora span:nth-child(1) {{
        width: 38vw; height: 38vw;
        top: -10%; left: -8%;
        background: var(--blob-a);
    }}
    .pp-aurora span:nth-child(2) {{
        width: 30vw; height: 30vw;
        top: 15%; right: -10%;
        background: var(--blob-b);
    }}
    .pp-aurora span:nth-child(3) {{
        width: 34vw; height: 34vw;
        bottom: -14%; left: 20%;
        background: var(--blob-c);
    }}

    .block-container {{
        max-width: 900px;
        padding-top: 1rem;
        padding-bottom: 1.5rem;
    }}

    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0.5rem;
    }}

    .glass {{
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        box-shadow: 0 8px 32px var(--glass-shadow);
    }}

    /* ---------- Hero: logo only, enlarged, no duplicate text heading ---------- */
    .pp-hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 2px;
        padding: 20px 24px 16px;
        margin-bottom: 14px;
    }}
    .pp-hero img {{
        width: clamp(110px, 18vw, 160px);
        height: auto;
    }}
    .pp-hero .pp-tagline {{
        font-weight: 500;
        font-size: clamp(12px, 1.8vw, 14px);
        color: var(--text-muted);
        margin: 0;
        letter-spacing: 0.4px;
    }}

    /* ---------- Sidebar: transparent-out ALL of Streamlit's own layered
       backgrounds first (they sit on top of a flat grey, blocking the
       aurora from showing through), then apply the glass tint once on the
       outermost layer so it matches the hero panel's vividness. ---------- */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
        background: transparent !important;
    }}
    section[data-testid="stSidebar"] > div:first-child {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border-right: 1px solid var(--glass-border);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text-color) !important;
    }}
    .pp-sidebar-logo {{
        display: flex;
        justify-content: center;
        padding: 4px 0 2px;
    }}
    .pp-sidebar-logo img {{
        width: 110px;
        height: auto;
    }}

    .pp-section-label {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        font-size: 12.5px;
        letter-spacing: 0.5px;
        color: var(--accent-strong);
        margin-top: 14px;
        margin-bottom: 6px;
    }}
    .pp-icon {{
        display: inline-flex;
        color: var(--accent-strong);
    }}
    .pp-icon svg {{ display: block; }}

    /* File uploader: flatten to a simple, non-blurred glass box so the
       drag-and-drop label text can't double-render. */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
        background: var(--input-bg) !important;
        border: 1.5px dashed var(--glass-border) !important;
        border-radius: 14px !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {{
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        color: var(--text-color) !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {{
        background: linear-gradient(135deg, var(--accent-strong), var(--accent)) !important;
        color: #FFFFFF !important;
        border-color: transparent !important;
    }}
    /* The default file-chip preview resists every CSS override attempted
       (name/size text always renders on its own white background no matter
       what we set here) -- simplest reliable fix is to hide it and render
       our own file list in Python instead (see app code below). */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {{
        display: none !important;
    }}
    /* Nuclear option: testid-based targeting kept missing this element entirely
       (display:none had zero effect), so force dark, readable text on EVERY
       element inside the dropzone regardless of its actual tag/class/testid. */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {{
        color: #1D1B2E !important;
    }}
    /* Safety net: hide ANY leftover element with an inline white/near-white
       background inside the uploader area, regardless of its testid/class --
       this is what was showing up as a pale "fog" box after the above rule. */
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [style*="background-color: rgb(255"],
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [style*="background: rgb(255"],
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [style*="background-color: #fff" i],
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] [style*="background-color: white" i] {{
        display: none !important;
    }}

    /* ---------- Buttons ---------- */
    .stButton > button {{
        background: linear-gradient(135deg, var(--accent-strong), var(--accent));
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.55rem 1rem;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 16px var(--glass-shadow);
    }}
    .stButton > button p {{ color: #FFFFFF !important; }}

    /* ---------- Chat card & messages ---------- */
    .pp-chat-card {{
        padding: 16px clamp(14px, 4vw, 30px);
        margin-bottom: 14px;
        min-height: 90px;
    }}
    div[data-testid="stChatMessage"] {{
        border-radius: 16px;
        border: 1px solid var(--glass-border);
        background: var(--input-bg);
    }}
    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] div {{
        color: var(--text-color) !important;
    }}
    div[data-testid="stChatMessage"] img {{
        border-radius: 50% !important;
        object-fit: cover;
        background: transparent !important;
    }}
    div[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"] {{
        background: transparent !important;
    }}

    /* ---------- Chat input: bigger, single clean field.
       Broadened selectors ([data-testid*="ChatInput"], nested wrapper divs)
       because the visible grey pill is the wrapper around the textarea,
       not just the textarea itself. ---------- */
    [data-testid*="ChatInput"] {{
        background: transparent !important;
    }}
    [data-testid*="ChatInput"] > div,
    [data-testid*="ChatInput"] div[data-baseweb],
    [data-testid*="ChatInput"] textarea {{
        background: var(--input-bg) !important;
        color: var(--text-color) !important;
        border-radius: 18px !important;
    }}
    [data-testid*="ChatInput"] textarea {{
        border: 1.5px solid var(--glass-border) !important;
        font-size: 16px !important;
        min-height: 56px !important;
        padding: 14px 18px !important;
    }}
    [data-testid*="ChatInput"] textarea::placeholder {{
        color: var(--text-muted) !important;
        opacity: 1 !important;
    }}
    [data-testid*="ChatInput"] button {{
        background: linear-gradient(135deg, var(--accent-strong), var(--accent)) !important;
    }}

    /* ---------- Footer bar (the fixed bottom container holding the chat
       input): was rendering with Streamlit's own hardcoded dark background,
       disconnected from the aurora page behind it. Give it the same glass
       treatment as the sidebar/menu instead. ---------- */
    [data-testid="stBottom"] {{
        background: transparent !important;
    }}
    [data-testid="stBottom"] > div {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border-top: 1px solid var(--glass-border);
    }}

    /* ---------- Sliders: primaryColor in .streamlit/config.toml already
       fixes this at the source; these rules are a CSS-level backup in case
       an older Streamlit version still paints the old accent inline. ---------- */
    [data-testid="stSlider"] div[style*="rgb(255, 75, 75)"],
    [data-testid="stSlider"] div[style*="rgb(255,75,75)"] {{
        background-color: var(--accent-strong) !important;
    }}
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div {{
        background: var(--accent-strong) !important;
    }}
    [data-testid="stSlider"] [role="slider"] {{
        background-color: var(--accent-strong) !important;
        border-color: var(--accent-strong) !important;
    }}
    [data-testid="stSlider"] [data-testid="stTickBarMin"],
    [data-testid="stSlider"] [data-testid="stTickBarMax"],
    [data-testid="stSlider"] [data-testid="stThumbValue"] {{
        color: var(--text-color) !important;
    }}

    /* ---------- Empty-state banner (replaces st.info, no emoji) ---------- */
    .pp-empty-state {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 20px 22px;
        border-radius: 18px;
    }}
    .pp-empty-state .pp-icon {{
        color: var(--accent);
        flex-shrink: 0;
    }}
    .pp-empty-state p {{
        margin: 0;
        color: var(--text-muted);
        font-weight: 500;
        font-size: 14.5px;
    }}

    .pp-doc-item, .pp-source-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        margin-bottom: 6px;
    }}

    hr {{ border-top: 1px solid var(--glass-border); }}

    [data-testid="stExpander"] {{
        background: var(--input-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 14px !important;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] * {{
        color: var(--text-color) !important;
        opacity: 1 !important;
    }}
    [data-testid="stExpander"] [data-testid="stCaptionContainer"],
    [data-testid="stExpander"] [data-testid="stCaptionContainer"] * {{
        color: var(--text-muted) !important;
        opacity: 1 !important;
    }}
    [data-testid="stExpanderDetails"] {{
        background: transparent !important;
    }}

    @media (max-width: 640px) {{
        .block-container {{ padding-left: 0.6rem; padding-right: 0.6rem; }}
        .pp-hero {{ padding: 26px 10px 18px; }}
    }}
    </style>

    <div class="pp-aurora"><span></span><span></span><span></span></div>

    <div class="pp-hero glass">
        <img src="data:image/png;base64,{WORDMARK_B64}" />
        <p class="pp-tagline">RAG DOCUMENT Q&amp;A ASSISTANT &middot; LANGCHAIN + GEMINI</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
if "session" not in st.session_state:
    st.session_state.session = PaperPilotSession()
if "chat" not in st.session_state:
    st.session_state.chat = []  # list of {role, content, sources}

session: PaperPilotSession = st.session_state.session

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        f'<div class="pp-sidebar-logo"><img src="data:image/png;base64,{WORDMARK_B64}" /></div>',
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="pp-section-label">{icon("upload")} UPLOAD DOCUMENTS</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload one or more PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        for f in uploaded_files:
            size_mb = f.size / (1024 * 1024)
            st.markdown(
                f'<div class="pp-doc-item">{icon("file")}<span>{f.name} '
                f'&middot; {size_mb:.1f} MB</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown(f'<div class="pp-section-label">{icon("sliders")} CHUNKING SETTINGS</div>', unsafe_allow_html=True)
    chunk_size = st.slider("Chunk size", min_value=300, max_value=2000, value=1500, step=100)
    chunk_overlap = st.slider("Chunk overlap", min_value=0, max_value=500, value=100, step=50)

    if st.button("Process documents", use_container_width=True, icon=":material/bolt:"):
        if not uploaded_files:
            st.warning("Please upload at least one PDF file.")
        else:
            session.chunk_size = chunk_size
            session.chunk_overlap = chunk_overlap
            with st.spinner("Reading and indexing your documents..."):
                tmp_paths = []
                for f in uploaded_files:
                    tmp_path = os.path.join(tempfile.gettempdir(), f.name)
                    with open(tmp_path, "wb") as out:
                        out.write(f.getbuffer())
                    tmp_paths.append(tmp_path)
                try:
                    session.add_documents(tmp_paths)
                    st.success(f"{len(tmp_paths)} document(s) indexed successfully.")
                except ValueError as e:
                    st.error(str(e))

    if session.indexed_files:
        st.markdown('<div class="pp-section-label">INDEXED DOCUMENTS</div>', unsafe_allow_html=True)
        for fname in session.indexed_files:
            st.markdown(f'<div class="pp-doc-item">{icon("file")}<span>{fname}</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("Reset session", use_container_width=True, icon=":material/restart_alt:"):
        session.reset()
        st.session_state.chat = []
        st.rerun()

# ---------- Main chat area ----------
if not session.indexed_files:
    st.markdown(
        f'<div class="glass pp-empty-state">{icon("compass")}<p>Upload a PDF in the sidebar, then click <b>Process documents</b> to start asking questions.</p></div>',
        unsafe_allow_html=True,
    )

for msg in st.session_state.chat:
    avatar = LOGO_ICON_PATH if msg["role"] == "assistant" else USER_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("View answer sources"):
                for s in msg["sources"]:
                    st.markdown(
                        f'<div class="pp-source-item">{icon("link")}<b>{s["file"]} &mdash; page {s["page"]}</b></div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(s["snippet"])

question = st.chat_input("Ask a question about your documents...")

if question:
    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=LOGO_ICON_PATH):
        with st.spinner("PaperPilot is reading your documents..."):
            try:
                result = session.ask(question)
                answer = result["answer"]
                sources = result["sources"]
            except ValueError as e:
                answer = str(e)
                sources = []
        st.markdown(answer)
        if sources:
            with st.expander("View answer sources"):
                for s in sources:
                    st.markdown(
                        f'<div class="pp-source-item">{icon("link")}<b>{s["file"]} &mdash; page {s["page"]}</b></div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(s["snippet"])

    st.session_state.chat.append({"role": "assistant", "content": answer, "sources": sources})
    st.rerun()