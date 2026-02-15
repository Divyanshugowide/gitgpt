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
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
.main-header {
    font-size: 2.4rem;
    font-weight: 700;
    color: #1f77b4;
    margin-bottom: 0.1rem;
}
.sub-header {
    font-size: 1.1rem;
    color: #888;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 0.75rem;
    color: white;
    text-align: center;
}
.info-box {
    background-color: #e7f3ff;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
}
.success-box {
    background-color: #d4edda;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
    margin: 0.5rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)

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

st.markdown('<div class="main-header">🔍 GitGPT — Repository Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Drop your repository, get architecture diagrams & ask anything about the code.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Configuration")
    provider_name = agent.provider_display
    st.info(f"Provider: **{provider_name}**. Configured via `.env` file.")

    st.markdown("---")

    st.header("📂 Load Repository")

    source_type = st.radio(
        "Source",
        ["📁 Local Path", "🌐 Git URL"],
        horizontal=True,
        help="Load from a local folder or clone from a remote Git repository.",
    )

    if source_type == "📁 Local Path":
        repo_input = st.text_input(
            "Repository path",
            value="",
            placeholder="e.g. D:/projects/my-app",
            help="Absolute path to the repository root folder.",
        )
    else:
        repo_input = st.text_input(
            "Git repository URL",
            value="",
            placeholder="e.g. https://github.com/user/repo",
            help="HTTPS or SSH URL of a public/private Git repository.",
        )
        branch_input = st.text_input(
            "Branch (optional)",
            value="",
            placeholder="main",
            help="Leave blank to clone the default branch.",
        )

    load_btn = st.button("🔄 Scan Repository", use_container_width=True)

    if load_btn and repo_input:
        if source_type == "📁 Local Path":
            if os.path.isdir(repo_input):
                with st.spinner("Scanning files & building project summary..."):
                    stats = agent.load_repository(repo_input)
                    st.session_state.repo_loaded = True
                    st.session_state.repo_stats = stats
                    st.session_state.diagram_result = None
                    st.session_state.chat_history = []
                st.success(f"Loaded {stats['total_files']} files!")
            else:
                st.error("Invalid path. Please provide a valid directory.")
        else:
            # Git URL
            if not agent.is_git_url(repo_input):
                st.error("That doesn't look like a Git URL. Please provide a valid URL.")
            else:
                branch = branch_input.strip() if branch_input.strip() else None
                try:
                    with st.spinner("Cloning repository & scanning files..."):
                        stats = agent.load_from_url(repo_input, branch=branch)
                        st.session_state.repo_loaded = True
                        st.session_state.repo_stats = stats
                        st.session_state.diagram_result = None
                        st.session_state.chat_history = []
                    st.success(f"Cloned & loaded {stats['total_files']} files!")
                except RuntimeError as e:
                    st.error(str(e))

    if st.session_state.repo_loaded:
        stats = st.session_state.repo_stats
        st.markdown("---")
        st.header("📊 Repo Stats")
        if stats.get("git_url"):
            st.caption(f"🌐 {stats['git_url']}")
        st.metric("Total Files", stats.get("total_files", 0))
        langs = stats.get("languages", {})
        if langs:
            for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True)[:8]:
                st.text(f"  {lang}: {count} files")

    st.markdown("---")
    st.header("🔧 Pipeline")
    st.markdown(
        """
1. Repository Scan
2. File Indexing
3. Project Summary (GPT)
4. Question Answering / Diagram Generation
5. Mermaid Rendering
"""
    )

    if st.button("🗑️ Clear All", use_container_width=True):
        # Clean up any cloned repo temp files
        if hasattr(st.session_state.agent, 'cleanup_clone'):
            st.session_state.agent.cleanup_clone()
        st.session_state.repo_loaded = False
        st.session_state.repo_stats = {}
        st.session_state.diagram_result = None
        st.session_state.chat_history = []
        st.session_state.agent = GitGPTAgent()
        st.success("Cleared!")

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
        st.warning("👈 Load a repository from the sidebar first.")
    else:
        st.subheader("Generate Diagram")
        col1, col2 = st.columns([1, 1])

        with col1:
            diagram_type = st.selectbox(
                "Diagram type",
                options=[dt.value for dt in DiagramType],
                index=0,
                help="Choose the kind of diagram to generate.",
            )
            focus_area = st.text_input(
                "Focus area (optional)",
                placeholder="e.g. authentication, payment flow, API layer",
                help="Narrow the diagram to a specific part of the system.",
            )

        with col2:
            gen_btn = st.button(
                "🚀 Generate Diagram",
                type="primary",
                use_container_width=True,
            )

        if gen_btn:
            with st.spinner("Analysing codebase and generating diagram..."):
                result = agent.generate_diagram(
                    diagram_type=diagram_type,
                    focus=focus_area,
                )
                st.session_state.diagram_result = result
            st.success("Diagram generated!")

        # --- Display result ---
        result = st.session_state.diagram_result
        if result:
            st.markdown("---")
            desc = result.get("description", "")
            if desc:
                st.markdown(f"**Description:** {desc}")

            diagram_code = result.get("diagram", "")

            # Visual preview
            is_mermaid = any(
                kw in diagram_code.lower()
                for kw in ["graph", "flowchart", "sequencediagram", "classdiagram", "statediagram"]
            )
            if is_mermaid and len(diagram_code.strip().splitlines()) > 1:
                st.markdown("#### 🖼️ Visual Preview")
                mermaid_html = f"""
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                    <script>mermaid.initialize({{startOnLoad: true, theme: 'default'}});</script>
                </head>
                <body style="background: white; padding: 16px;">
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
                    "⬇️ Download Diagram",
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
        st.warning("👈 Load a repository from the sidebar first.")
    else:
        st.subheader("Ask anything about your codebase")

        # Display chat history
        for entry in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(entry["question"])
            with st.chat_message("assistant"):
                st.markdown(entry["answer"])

        # Chat input
        question = st.chat_input("Ask a question about the code...")

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
        st.warning("👈 Load a repository from the sidebar first.")
    else:
        st.subheader("Project Summary")
        stats = st.session_state.repo_stats

        # Stats row
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Files", stats.get("total_files", 0))
        c2.metric("Languages", len(stats.get("languages", {})))
        top_lang = max(stats.get("languages", {"?": 0}), key=stats["languages"].get) if stats.get("languages") else "N/A"
        c3.metric("Primary Language", top_lang)

        st.markdown("---")

        st.markdown("#### 📝 AI-Generated Summary")
        st.markdown(stats.get("summary", "_No summary available._"))

        st.markdown("---")

        st.markdown("#### 📁 File Tree")
        file_tree = agent._get_file_tree()
        st.code(file_tree, language="text")

# ---------------------------------------------------------------------------
# Tab 4 – Documentation
# ---------------------------------------------------------------------------

with tab_docs:
    st.subheader("Documentation")
    st.markdown(
        """
### How to Use GitGPT

#### 1. Load Your Repository
Enter the **absolute path** to any local repository in the sidebar and click **Scan Repository**.
GitGPT will read all source files, skip binaries and build artifacts, and generate a project summary.

#### 2. Generate Architecture Diagrams
Go to the **Architecture Diagram** tab. Choose a diagram type:

| Type | Best For |
|------|----------|
| **ARCHITECTURE_DIAGRAM** | System components, services, modules |
| **FLOWCHART** | Processes, algorithms, workflows |
| **SEQUENCE_DIAGRAM** | API call flows, interactions |
| **DATA_FLOW_DIAGRAM** | Data pipelines, ETL |
| **CLASS_DIAGRAM** | Class relationships, OOP structure |

Optionally add a **focus area** to narrow the diagram to a specific part of the system.

#### 3. Ask Questions
Go to the **Ask About Code** tab and type any question:
- *"What does this project do?"*
- *"How is authentication implemented?"*
- *"What databases are used?"*
- *"Explain the payment flow"*
- *"What are the main API endpoints?"*
- *"What external services does this project integrate with?"*

#### 4. Review Project Summary
The **Project Summary** tab shows the AI-generated overview, file stats, and full file tree.

### Supported Languages
Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, C#, Ruby, PHP, Swift, Kotlin, Dart, Scala, SQL, HTML/CSS, YAML, JSON, Dockerfile, Terraform, and more.

### Tips
- ✅ Point it to the **root** of your repo for best results
- ✅ The more code in the repo, the richer the diagrams
- ✅ Use the focus area for large repos to get targeted diagrams
- ❌ Don't point it at node_modules or build output folders (they're auto-skipped)
"""
    )
    st.markdown(
        '<div class="info-box"><strong>💡 Pro Tip:</strong> For monorepos, set the focus area to a specific service name to get a cleaner diagram.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #888; padding: 1rem 0;">'
    f"Powered by {agent.provider_display} | GitGPT v1.0"
    "</div>",
    unsafe_allow_html=True,
)
