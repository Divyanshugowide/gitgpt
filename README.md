<div align="center">

<img src="https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI">
<img src="https://img.shields.io/badge/Hugging%20Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Hugging Face">
<img src="https://img.shields.io/badge/Mermaid-FF3670?style=for-the-badge&logo=mermaid&logoColor=white" alt="Mermaid">

<br><br>

# 🔍 GitGPT

### AI-Powered Repository Intelligence

*Drop any codebase — local or remote — and instantly get architecture diagrams, AI-generated summaries, and natural language Q&A about your code.*

<br>

[Getting Started](#-getting-started) •
[Features](#-features) •
[Configuration](#%EF%B8%8F-configuration) •
[Screenshots](#-screenshots) •
[Contributing](#-contributing)

<br>

---

</div>

<br>

## 🎯 What is GitGPT?

**GitGPT** is an intelligent code analysis tool that reads your entire repository, understands its structure, and lets you interact with it using natural language. Whether you're onboarding onto a new codebase, creating documentation, or trying to understand complex architectures — GitGPT has you covered.

> **Works with any Git repository** — paste a GitHub URL or point to a local folder. That's it.

<br>

## ✨ Features

| Feature | Description |
|:--------|:------------|
| 🌐 **Remote Repository Support** | Clone and analyze any public/private Git repository by URL |
| 📁 **Local Repository Support** | Point to any local folder on your machine |
| 📐 **Architecture Diagrams** | Auto-generate Mermaid diagrams — flowchart, sequence, class, data flow, architecture |
| 💬 **Code Q&A** | Ask natural language questions and get detailed answers with file references |
| 📋 **Project Summary** | AI-generated overview of purpose, tech stack, and structure |
| 🔄 **Multi-Provider** | Switch between OpenAI (GPT) and Hugging Face (free open-source models) with one env variable |
| 🖥️ **Interactive UI** | Beautiful Streamlit web interface with live diagram rendering |
| ⚡ **Smart Scanning** | Skips binaries, build artifacts, and `node_modules` automatically |

<br>

## 📋 Supported Languages

<div align="center">

`Python` `JavaScript` `TypeScript` `Java` `Go` `Rust` `C` `C++` `C#` `Ruby` `PHP` `Swift` `Kotlin` `Dart` `Scala` `SQL` `HTML` `CSS` `SCSS` `YAML` `JSON` `XML` `Bash` `PowerShell` `Dockerfile` `Terraform` `Protobuf` `GraphQL` `TOML` `Markdown`

</div>

<br>

## 🛠️ Tech Stack

| Technology | Role |
|:-----------|:-----|
| **Python 3.8+** | Core language |
| **OpenAI API** | GPT models for code analysis & diagram generation |
| **Hugging Face Inference API** | Free alternative — Mistral, Llama, Gemma, Zephyr, etc. |
| **Streamlit** | Web-based interactive UI |
| **Mermaid.js** | Architecture diagram rendering |
| **Git** | Remote repository cloning |

<br>

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Git** (for cloning remote repos)
- An **OpenAI API key** or a free **[Hugging Face token](https://huggingface.co/settings/tokens)**

### Installation

```bash
# 1. Clone this repository
git clone https://github.com/Divyanshugowide/gitgpt.git
cd gitgpt

# 2. Create a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API key(s)
```

### Run the App

#### 🖥️ Web UI (Recommended)

```bash
streamlit run gitgptui.py
```

Opens at **http://localhost:8501** — then:

1. Choose **Local Path** or **Git URL** in the sidebar
2. Paste a GitHub URL like `https://github.com/user/repo` or enter a local path
3. Click **Scan Repository**
4. Explore diagrams, ask questions, and review the AI summary

#### ⌨️ CLI

```bash
python gitgpt_agent.py
```

Scans the current directory, prints a summary, generates an architecture diagram, and answers a sample question.

<br>

## ⚙️ Configuration

All settings live in the **`.env`** file. Copy `.env.example` to get started.

### 🔀 Provider Switch

```env
# Choose your LLM backend: "openai" or "huggingface"
LLM_PROVIDER=openai
```

### OpenAI Settings

> Used when `LLM_PROVIDER=openai`

| Variable | Description | Default |
|:---------|:------------|:--------|
| `OPENAI_API_KEY` | Your OpenAI API key | *(required)* |
| `OPENAI_MODEL_ID` | Model to use | `gpt-5.2` |

### Hugging Face Settings (Free)

> Used when `LLM_PROVIDER=huggingface`

| Variable | Description | Default |
|:---------|:------------|:--------|
| `HF_API_KEY` | Your [HF token](https://huggingface.co/settings/tokens) (free) | *(required)* |
| `HF_MODEL_ID` | Model ID on HF Hub | `mistralai/Mistral-7B-Instruct-v0.3` |
| `HF_API_URL` | Inference API base URL | `https://api-inference.huggingface.co/models/` |

### Shared

| Variable | Description | Default |
|:---------|:------------|:--------|
| `MAX_TOKENS` | Max response tokens | `4096` |
| `TEMPERATURE` | Creativity (0.0 – 1.0) | `0.7` |

<details>
<summary><strong>💡 Quick switch to Hugging Face (free, no credit card)</strong></summary>

<br>

1. Get a free token at https://huggingface.co/settings/tokens
2. Update your `.env`:

```env
LLM_PROVIDER=huggingface
HF_API_KEY=hf_your-token-here
HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3
```

3. Restart the app — done!

**Recommended free models:**

| Model | Size | Notes |
|:------|:-----|:------|
| `mistralai/Mistral-7B-Instruct-v0.3` | 7B | Great all-rounder |
| `HuggingFaceH4/zephyr-7b-beta` | 7B | Strong instruction following |
| `google/gemma-2-2b-it` | 2B | Lightweight & fast |
| `meta-llama/Llama-3.2-3B-Instruct` | 3B | Meta's compact model |

</details>

<br>

## 📐 Diagram Types

| Type | Best For | Mermaid Syntax |
|:-----|:---------|:---------------|
| **ARCHITECTURE_DIAGRAM** | System components, services, modules | `graph TB` |
| **FLOWCHART** | Processes, algorithms, workflows | `flowchart TD/LR` |
| **SEQUENCE_DIAGRAM** | API call flows, interactions | `sequenceDiagram` |
| **DATA_FLOW_DIAGRAM** | Data pipelines, ETL | `graph LR` |
| **CLASS_DIAGRAM** | Class relationships, OOP structure | `classDiagram` |

<br>

## 📁 Project Structure

```
gitgpt/
├── gitgpt_agent.py      # Core agent — repo scanning, cloning, LLM calls, diagram generation
├── gitgptui.py           # Streamlit web UI — sidebar, tabs, Mermaid rendering
├── requirements.txt      # Python dependencies
├── .env                  # Your environment variables (git-ignored)
├── .env.example          # Template for .env
├── .gitignore            # Git ignore rules
└── README.md             # You are here
```

<br>

## 🧠 How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Local Path or  │────▶│  GitGPT Agent    │────▶│  LLM Provider   │
│  Git URL        │     │  - Scan files    │     │  - OpenAI GPT   │
│                 │     │  - Build context │     │  - Hugging Face │
└─────────────────┘     │  - Generate      │     └─────────────────┘
                        │    prompts       │              │
                        └──────────────────┘              │
                                 ▲                        │
                                 │                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Streamlit UI    │◀────│  AI Response    │
                        │  - Diagrams      │     │  - Summaries    │
                        │  - Chat Q&A      │     │  - Mermaid code │
                        │  - Summary       │     │  - Answers      │
                        └──────────────────┘     └─────────────────┘
```

<br>

## 💡 Tips & Best Practices

- ✅ Point to the **root** of a repository for the best results
- ✅ Use the **focus area** field to narrow diagrams for large codebases
- ✅ The more code in the repo, the richer the generated diagrams
- ✅ For monorepos, set focus to a specific service name
- ⚡ Remote repos use **shallow clone** (`--depth 1`) for speed
- 🚫 `node_modules`, `build/`, `dist/`, and binaries are auto-skipped

<br>

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

<br>

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

<br>

---

<div align="center">

**Built with ❤️ by [Divyanshu](https://github.com/Divyanshugowide)**

*If you found this useful, give it a ⭐ on GitHub!*

</div>
