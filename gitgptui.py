import streamlit as st
import streamlit.components.v1 as components
import os

from gitgpt_agent import GitGPTAgent, DiagramType

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GitGPT — Repository Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Professional CSS Theme
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
/* ---- Import Google Font ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ---- Global ---- */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---- Hide Streamlit defaults ---- */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* Keep header visible so sidebar toggle button works */
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #e0e0ff;
}

/* ---- Hero Header ---- */
.hero-container {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    margin-bottom: 0.5rem;
}
.hero-logo {
    font-size: 3rem;
    margin-bottom: 0.2rem;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 1rem;
    color: #8888aa;
    margin-top: 0.3rem;
    font-weight: 400;
}
.hero-divider {
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 3px;
    margin: 0.8rem auto 0 auto;
}

/* ---- Sidebar Brand ---- */
.sidebar-brand {
    text-align: center;
    padding: 0.8rem 0 0.5rem 0;
}
.sidebar-brand-title {
    font-size: 1.3rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sidebar-brand-sub {
    font-size: 0.7rem;
    color: #6c6c8a;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ---- Provider Pill ---- */
.provider-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(102, 126, 234, 0.12);
    border: 1px solid rgba(102, 126, 234, 0.25);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    color: #99aaff;
    margin: 0.5rem auto;
    width: fit-content;
}
.provider-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #4caf50;
    display: inline-block;
}

/* ---- Section Labels ---- */
.section-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #6c6c8a;
    margin: 1.2rem 0 0.5rem 0;
}

/* ---- Stat Chips ---- */
.stat-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 0.5rem 0;
}
.stat-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 0.75rem;
    color: #c0c0d8;
    flex: 1;
    text-align: center;
    min-width: 80px;
}
.stat-chip strong {
    display: block;
    font-size: 1.1rem;
    color: #e0e0ff;
    margin-bottom: 2px;
}

/* ---- Repo URL Badge ---- */
.repo-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(76, 175, 80, 0.08);
    border: 1px solid rgba(76, 175, 80, 0.2);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.72rem;
    color: #81c784;
    word-break: break-all;
    margin: 0.4rem 0;
}

/* ---- Lang Tags ---- */
.lang-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 0.3rem;
}
.lang-tag {
    background: rgba(118, 75, 162, 0.15);
    border: 1px solid rgba(118, 75, 162, 0.25);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.65rem;
    color: #c0a0e0;
}

/* ---- Tabs Styling ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: rgba(255,255,255,0.02);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2)) !important;
    border: none !important;
}

/* ---- Empty State ---- */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #6c6c8a;
}
.empty-state-icon {
    font-size: 3.5rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}
.empty-state-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #9999bb;
    margin-bottom: 0.3rem;
}
.empty-state-text {
    font-size: 0.9rem;
    color: #6c6c8a;
}

/* ---- Chat bubbles ---- */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 0.5rem;
}

/* ---- Buttons ---- */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.3px;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border: none !important;
}

/* ---- Metric Cards ---- */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.8rem;
}

/* ---- Download button ---- */
.stDownloadButton > button {
    border-radius: 8px;
}

/* ---- Footer ---- */
.pro-footer {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin-top: 2rem;
}
.pro-footer-text {
    font-size: 0.75rem;
    color: #555570;
}
.pro-footer-text a {
    color: #667eea;
    text-decoration: none;
}
.pro-footer-brand {
    font-size: 0.65rem;
    color: #444460;
    margin-top: 4px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Donate dialog (native Streamlit modal)
# ---------------------------------------------------------------------------

@st.dialog("☕ Buy Me a Coffee")
def show_donate_dialog():
    st.markdown(
        "<div style='text-align:center; font-size:2.5rem;'>☕💖</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align:center; margin:0;'>Thank You So Much!</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#8888aa; font-size:0.9rem; line-height:1.6;'>"
        "I'm truly grateful that you're considering supporting my work.<br>"
        "Every small contribution fuels late-night coding sessions "
        "and keeps this project alive. You're amazing! 🙏</p>",
        unsafe_allow_html=True,
    )

    qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "qr.jpeg")
    if os.path.exists(qr_path):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(qr_path, caption="Scan with any UPI app to donate", width=220)
    else:
        st.warning("QR code image not found at assets/qr.jpeg")

    st.markdown(
        "<p style='text-align:center; font-size:0.75rem; color:#667eea; font-weight:500;'>"
        "Thank you for your generosity! 💜</p>",
        unsafe_allow_html=True,
    )

    if st.button("Close", use_container_width=True):
        st.rerun()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "agent" not in st.session_state:
    st.session_state.agent = GitGPTAgent()
if "repo_loaded" not in st.session_state:
    st.session_state.repo_loaded = False
if "repo_stats" not in st.session_state:
    st.session_state.repo_stats = {}
if "diagram_result" not in st.session_state:
    st.session_state.diagram_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

agent: GitGPTAgent = st.session_state.agent

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-container">
        <div class="hero-logo">🔍</div>
        <h1 class="hero-title">GitGPT</h1>
        <p class="hero-subtitle">Drop a repository. Get instant intelligence.</p>
        <div class="hero-divider"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # Brand
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🔍 GitGPT</div>
            <div class="sidebar-brand-sub">Repository Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Source selection
    st.markdown('<div class="section-label">📂 Repository Source</div>', unsafe_allow_html=True)

    source_type = st.radio(
        "Source",
        ["📁 Local Path", "🌐 Git URL"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if source_type == "📁 Local Path":
        repo_input = st.text_input(
            "Repository path",
            value="",
            placeholder="D:/projects/my-app",
            label_visibility="collapsed",
        )
    else:
        repo_input = st.text_input(
            "Git repository URL",
            value="",
            placeholder="https://github.com/user/repo",
            label_visibility="collapsed",
        )
        branch_input = st.text_input(
            "Branch",
            value="",
            placeholder="Branch (optional)",
            label_visibility="collapsed",
        )

    load_btn = st.button("⚡ Scan Repository", use_container_width=True, type="primary")

    if load_btn and repo_input:
        if source_type == "📁 Local Path":
            if os.path.isdir(repo_input):
                with st.spinner("Scanning files & building project summary..."):
                    stats = agent.load_repository(repo_input)
                    st.session_state.repo_loaded = True
                    st.session_state.repo_stats = stats
                    st.session_state.diagram_result = None
                    st.session_state.chat_history = []
                st.success(f"✅ Loaded **{stats['total_files']}** files")
            else:
                st.error("Invalid path. Please provide a valid directory.")
        else:
            if not agent.is_git_url(repo_input):
                st.error("Invalid Git URL.")
            else:
                branch = branch_input.strip() if branch_input.strip() else None
                try:
                    with st.spinner("Cloning & scanning repository..."):
                        stats = agent.load_from_url(repo_input, branch=branch)
                        st.session_state.repo_loaded = True
                        st.session_state.repo_stats = stats
                        st.session_state.diagram_result = None
                        st.session_state.chat_history = []
                    st.success(f"✅ Cloned & loaded **{stats['total_files']}** files")
                except RuntimeError as e:
                    st.error(str(e))

    # Repo Stats
    if st.session_state.repo_loaded:
        stats = st.session_state.repo_stats

        st.markdown("---")
        st.markdown('<div class="section-label">📊 Repository Stats</div>', unsafe_allow_html=True)

        if stats.get("git_url"):
            st.markdown(
                f'<div class="repo-badge">🌐 {stats["git_url"]}</div>',
                unsafe_allow_html=True,
            )

        total = stats.get("total_files", 0)
        lang_count = len(stats.get("languages", {}))
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-chip"><strong>{total}</strong>Files</div>
                <div class="stat-chip"><strong>{lang_count}</strong>Languages</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        langs = stats.get("languages", {})
        if langs:
            tags = "".join(
                f'<span class="lang-tag">{lang} ({count})</span>'
                for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            st.markdown(f'<div class="lang-tags">{tags}</div>', unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🗑️ Clear All", use_container_width=True):
        if hasattr(st.session_state.agent, 'cleanup_clone'):
            st.session_state.agent.cleanup_clone()
        st.session_state.repo_loaded = False
        st.session_state.repo_stats = {}
        st.session_state.diagram_result = None
        st.session_state.chat_history = []
        st.session_state.agent = GitGPTAgent()
        st.rerun()

    # ---- Buy Me a Coffee ----
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    if st.button("☕ Buy Me a Coffee", use_container_width=True):
        show_donate_dialog()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_diagram, tab_chat, tab_summary, tab_docs = st.tabs(
    ["📐 Architecture Diagram", "💬 Ask About Code", "📋 Project Summary", "📖 Documentation"]
)

# ---------------------------------------------------------------------------
# Tab 1 – Architecture Diagram
# ---------------------------------------------------------------------------

with tab_diagram:
    if not st.session_state.repo_loaded:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📐</div>
                <div class="empty-state-title">No repository loaded</div>
                <div class="empty-state-text">Load a repository from the sidebar to generate architecture diagrams.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            diagram_type = st.selectbox(
                "Diagram type",
                options=[dt.value for dt in DiagramType],
                index=0,
            )
        with col2:
            focus_area = st.text_input(
                "Focus area (optional)",
                placeholder="e.g. authentication, payment flow",
            )
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            gen_btn = st.button("🚀 Generate", type="primary", use_container_width=True)

        if gen_btn:
            with st.spinner("Analysing codebase & generating diagram..."):
                result = agent.generate_diagram(
                    diagram_type=diagram_type,
                    focus=focus_area,
                )
                st.session_state.diagram_result = result
            st.success("Diagram generated!")

        result = st.session_state.diagram_result
        if result:
            desc = result.get("description", "")
            if desc:
                st.markdown(f"> {desc}")

            diagram_code = result.get("diagram", "")

            is_mermaid = any(
                kw in diagram_code.lower()
                for kw in ["graph", "flowchart", "sequencediagram", "classdiagram", "statediagram"]
            )
            if is_mermaid and len(diagram_code.strip().splitlines()) > 1:
                mermaid_html = f"""
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad: true, theme: 'dark'}});</script>
                </head>
                <body style="background: transparent; padding: 20px;">
                    <div class="mermaid">
{diagram_code}
                    </div>
                </body>
                </html>
                """
                components.html(mermaid_html, height=520, scrolling=True)
            elif not diagram_code.strip():
                st.warning("No diagram content generated.")

            diag_tab, bp_tab = st.tabs(["📝 Diagram Code", "🗂️ Blueprint"])

            with diag_tab:
                st.code(diagram_code, language="text")
                st.download_button(
                    "⬇️ Download .mmd",
                    data=diagram_code,
                    file_name="architecture_diagram.mmd",
                    mime="text/plain",
                    use_container_width=True,
                )

            with bp_tab:
                blueprint = result.get("blueprint", {})
                meta = blueprint.get("metadata", {})
                c1, c2, c3 = st.columns(3)
                c1.metric("Nodes", meta.get("node_count", 0))
                c2.metric("Edges", meta.get("edge_count", 0))
                c3.metric("Layout", blueprint.get("layout", "N/A"))
                st.json(blueprint)

# ---------------------------------------------------------------------------
# Tab 2 – Ask About Code
# ---------------------------------------------------------------------------

with tab_chat:
    if not st.session_state.repo_loaded:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-title">No repository loaded</div>
                <div class="empty-state-text">Load a repository from the sidebar to start asking questions about the code.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Display chat history
        for entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(entry["question"])
            with st.chat_message("assistant"):
                st.markdown(entry["answer"])

        # Chat input
        question = st.chat_input("Ask anything about the codebase...")

        if question:
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = agent.ask(question)
                st.markdown(answer)

            st.session_state.chat_history.append({
                "question": question,
                "answer": answer,
            })

# ---------------------------------------------------------------------------
# Tab 3 – Project Summary
# ---------------------------------------------------------------------------

with tab_summary:
    if not st.session_state.repo_loaded:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <div class="empty-state-title">No repository loaded</div>
                <div class="empty-state-text">Load a repository from the sidebar to view the AI-generated project summary.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        stats = st.session_state.repo_stats

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Files", stats.get("total_files", 0))
        c2.metric("Languages", len(stats.get("languages", {})))
        top_lang = max(stats.get("languages", {"?": 0}), key=stats["languages"].get) if stats.get("languages") else "N/A"
        c3.metric("Primary Language", top_lang)

        st.markdown("---")

        st.markdown("#### 📝 AI-Generated Summary")
        st.markdown(stats.get("summary", "_No summary available._"))

        st.markdown("---")

        with st.expander("📁 Full File Tree", expanded=False):
            file_tree = agent._get_file_tree()
            st.code(file_tree, language="text")

# ---------------------------------------------------------------------------
# Tab 4 – Documentation
# ---------------------------------------------------------------------------

with tab_docs:
    st.markdown(
        """
### 🚀 Quick Start

1. **Paste** a GitHub URL or local path in the sidebar
2. **Click** Scan Repository
3. **Explore** diagrams, ask questions, review summaries

---

### 📐 Diagram Types

| Type | Best For |
|:-----|:---------|
| `ARCHITECTURE_DIAGRAM` | System components, services, modules |
| `FLOWCHART` | Processes, algorithms, workflows |
| `SEQUENCE_DIAGRAM` | API call flows, interactions |
| `DATA_FLOW_DIAGRAM` | Data pipelines, ETL |
| `CLASS_DIAGRAM` | Class relationships, OOP structure |

---

### 💬 Example Questions

> *"What does this project do?"*
> *"How is authentication implemented?"*
> *"What databases are used?"*
> *"Explain the payment flow"*
> *"What are the main API endpoints?"*

---

### 📋 Supported Languages

Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, C#, Ruby, PHP,
Swift, Kotlin, Dart, Scala, SQL, HTML/CSS, YAML, JSON, Dockerfile, Terraform, and 10+ more.

---

### 💡 Tips

- ✅ Point to the **root** of your repo for best results
- ✅ Use **focus area** to narrow diagrams for large codebases
- ⚡ Remote repos use **shallow clone** for speed
- 🚫 `node_modules`, `build/`, `dist/` are auto-skipped
"""
    )



# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="pro-footer">
        <div class="pro-footer-text">
            Built with ❤️ by <a href="https://github.com/Divyanshugowide" target="_blank">Divyanshu</a> ·
            <a href="https://github.com/Divyanshugowide/gitgpt" target="_blank">GitHub</a>
        </div>
        <div class="pro-footer-brand">GitGPT v1.0</div>
    </div>
    """,
    unsafe_allow_html=True,
)
