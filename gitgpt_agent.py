import json
import os
import re
import fnmatch
import shutil
import subprocess
import tempfile
import requests
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Provider switch: "openai" or "huggingface"
llm_provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()

# OpenAI settings
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model_id = os.getenv("OPENAI_MODEL_ID", "gpt-5.2")

# Hugging Face settings
hf_api_key = os.getenv("HF_API_KEY")
hf_model_id = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
hf_api_url = os.getenv("HF_API_URL", "https://api-inference.huggingface.co/models/")

# Shared settings
max_tokens = int(os.getenv("MAX_TOKENS", os.getenv("OPENAI_MAX_TOKENS", "4096")))
temperature = float(os.getenv("TEMPERATURE", os.getenv("OPENAI_TEMPERATURE", "0.7")))

# ---------------------------------------------------------------------------
# File extension → language mapping
# ---------------------------------------------------------------------------

EXTENSION_MAP: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".kt": "kotlin",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".swift": "swift",
    ".dart": "dart",
    ".scala": "scala",
    ".r": "r",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".txt": "text",
    ".sh": "bash",
    ".bat": "batch",
    ".ps1": "powershell",
    ".dockerfile": "dockerfile",
    ".tf": "terraform",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".env": "text",
    ".gitignore": "text",
}

# Directories to always skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "env",
    ".idea", ".vscode", ".vs", "dist", "build", "out", "target",
    ".next", ".nuxt", "coverage", ".tox", ".mypy_cache", ".pytest_cache",
    "bin", "obj", ".terraform", ".eggs", "*.egg-info",
}

# Binary / large files to skip
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".avi", ".wav", ".pdf", ".zip", ".tar",
    ".gz", ".exe", ".dll", ".so", ".dylib", ".whl", ".pyc",
    ".class", ".jar", ".lock", ".min.js", ".min.css",
}

MAX_FILE_SIZE = 100_000  # 100 KB per file


class DiagramType(Enum):
    FLOWCHART = "FLOWCHART"
    ARCHITECTURE_DIAGRAM = "ARCHITECTURE_DIAGRAM"
    SEQUENCE_DIAGRAM = "SEQUENCE_DIAGRAM"
    DATA_FLOW_DIAGRAM = "DATA_FLOW_DIAGRAM"
    CLASS_DIAGRAM = "CLASS_DIAGRAM"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class GitGPTAgent:
    """
    AI agent that reads an entire repository, answers questions about it,
    and generates architecture diagrams — powered by OpenAI or Hugging Face.
    """

    def __init__(self):
        self.provider = llm_provider
        if self.provider == "openai":
            self.client = OpenAI(api_key=openai_api_key)
        else:
            self.client = None  # HuggingFace uses REST API
        self.repo_path: Optional[str] = None
        self.file_index: List[Dict[str, str]] = []  # [{path, language, content}]
        self.project_summary: str = ""
        self._cloned_dir: Optional[str] = None  # temp dir for cloned repos

    @property
    def provider_display(self) -> str:
        """Return a human-readable provider name."""
        if self.provider == "huggingface":
            return f"Hugging Face ({hf_model_id})"
        return f"OpenAI ({openai_model_id})"

    # ------------------------------------------------------------------
    # Git URL helpers
    # ------------------------------------------------------------------

    @staticmethod
    def is_git_url(path_or_url: str) -> bool:
        """Check if the input looks like a Git repository URL."""
        path_or_url = path_or_url.strip()
        if path_or_url.startswith(("http://", "https://", "git@", "ssh://", "git://")):
            return True
        if "github.com" in path_or_url or "gitlab.com" in path_or_url or "bitbucket.org" in path_or_url:
            return True
        return False

    def clone_repository(self, git_url: str, branch: Optional[str] = None) -> str:
        """
        Clone a remote Git repository to a temporary directory.

        Args:
            git_url: The Git clone URL (HTTPS or SSH).
            branch: Optional branch name to clone.

        Returns:
            The local path to the cloned repository.

        Raises:
            RuntimeError: If git clone fails.
        """
        # Clean up any previous clone
        self.cleanup_clone()

        # Create a temp directory
        tmp_dir = tempfile.mkdtemp(prefix="gitgpt_")
        self._cloned_dir = tmp_dir

        # Sanitize URL (remove trailing slashes, .git suffix is fine)
        git_url = git_url.strip().rstrip("/")

        # Build git clone command
        cmd = ["git", "clone", "--depth", "1"]  # shallow clone for speed
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([git_url, tmp_dir])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                raise RuntimeError(f"Git clone failed: {error_msg}")
        except subprocess.TimeoutExpired:
            self.cleanup_clone()
            raise RuntimeError("Git clone timed out after 120 seconds.")
        except FileNotFoundError:
            self.cleanup_clone()
            raise RuntimeError(
                "Git is not installed or not on PATH. "
                "Please install Git: https://git-scm.com/downloads"
            )

        return tmp_dir

    def cleanup_clone(self):
        """Remove the temporary cloned directory if it exists."""
        if self._cloned_dir and os.path.isdir(self._cloned_dir):
            try:
                shutil.rmtree(self._cloned_dir, ignore_errors=True)
            except Exception:
                pass
        self._cloned_dir = None

    def load_from_url(self, git_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Clone a remote repository and load it.

        Args:
            git_url: Git clone URL.
            branch: Optional branch to clone.

        Returns:
            Statistics about the scanned repo (same as load_repository).
        """
        local_path = self.clone_repository(git_url, branch)
        stats = self.load_repository(local_path)
        stats["source"] = "remote"
        stats["git_url"] = git_url
        return stats

    # ------------------------------------------------------------------
    # Repository scanning
    # ------------------------------------------------------------------

    def load_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Recursively scan the repository, read every eligible file,
        and build a project summary via GPT-5.2.

        Returns:
            Statistics about the scanned repo.
        """
        self.repo_path = os.path.abspath(repo_path)
        self.file_index = []

        stats: Dict[str, int] = {}

        for root, dirs, files in os.walk(self.repo_path):
            # Prune ignored directories in-place
            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIRS and not d.startswith(".")
            ]

            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()

                if ext in SKIP_EXTENSIONS:
                    continue

                # Dockerfile special case
                if fname.lower() == "dockerfile":
                    ext = ".dockerfile"

                language = EXTENSION_MAP.get(ext)
                if language is None:
                    continue

                try:
                    size = os.path.getsize(fpath)
                    if size > MAX_FILE_SIZE or size == 0:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception:
                    continue

                rel_path = os.path.relpath(fpath, self.repo_path)
                self.file_index.append({
                    "path": rel_path,
                    "language": language,
                    "content": content,
                })
                stats[language] = stats.get(language, 0) + 1

        # Build summary
        self.project_summary = self._build_project_summary()

        return {
            "repo_path": self.repo_path,
            "total_files": len(self.file_index),
            "languages": stats,
            "summary": self.project_summary,
        }

    # ------------------------------------------------------------------
    # Project summary
    # ------------------------------------------------------------------

    def _build_project_summary(self) -> str:
        """Ask GPT-5.2 to produce a concise summary of the project."""
        file_tree = self._get_file_tree()
        snippet = self._get_key_snippets(max_chars=12000)

        prompt = f"""You are a senior software engineer. Analyse the following repository and produce a concise project summary.

FILE TREE:
{file_tree}

KEY FILE CONTENTS (truncated):
{snippet}

Produce a summary that includes:
1. Project name / purpose
2. Tech stack (languages, frameworks, databases)
3. High-level architecture (services, modules, layers)
4. Entry points and important files
5. External dependencies and integrations

Be factual — only describe what is present in the code.
"""
        try:
            return self._call_gpt(prompt, temperature_override=0.3)
        except Exception as e:
            return f"(Could not generate summary: {e})"

    # ------------------------------------------------------------------
    # Ask a question
    # ------------------------------------------------------------------

    def ask(self, question: str) -> str:
        """
        Answer any question about the loaded repository.
        """
        if not self.file_index:
            return "No repository loaded. Please load a repository first."

        context = self._build_question_context(question)

        prompt = f"""You are an expert software engineer who has full access to a codebase.
Use ONLY the provided code context to answer the user's question.
If the answer is not in the code, say so.

PROJECT SUMMARY:
{self.project_summary}

RELEVANT CODE CONTEXT:
{context}

USER QUESTION:
{question}

Provide a clear, detailed answer. Include file paths and code references where applicable.
"""
        try:
            return self._call_gpt(prompt, temperature_override=0.4)
        except Exception as e:
            return f"Error: {e}"

    # ------------------------------------------------------------------
    # Generate architecture diagram
    # ------------------------------------------------------------------

    def generate_diagram(
        self,
        diagram_type: str = "ARCHITECTURE_DIAGRAM",
        focus: str = "",
    ) -> Dict[str, Any]:
        """
        Generate a Mermaid diagram for the loaded repository.

        Args:
            diagram_type: One of DiagramType values.
            focus: Optional focus area (e.g. "authentication flow").

        Returns:
            Dict with keys: diagram_type, diagram, description, blueprint.
        """
        if not self.file_index:
            return {
                "diagram_type": diagram_type,
                "diagram": "",
                "description": "No repository loaded.",
                "blueprint": {},
            }

        file_tree = self._get_file_tree()
        snippet = self._get_key_snippets(max_chars=10000)

        focus_text = f"\nFOCUS AREA: {focus}" if focus else ""

        # Step 1 — Blueprint
        blueprint_prompt = f"""You are an expert software architect. Analyse this repository and create a diagram blueprint.

DIAGRAM TYPE: {diagram_type}
{focus_text}

PROJECT SUMMARY:
{self.project_summary}

FILE TREE:
{file_tree}

KEY CODE:
{snippet}

Create a JSON blueprint with this structure:
{{
    "diagram_type": "{diagram_type}",
    "title": "<descriptive title>",
    "description": "<one-paragraph description>",
    "granularity": "high|medium|low",
    "layout": "top-down|left-right|layered",
    "nodes": [
        {{"id": "snake_case_id", "label": "Display Name", "type": "component|service|database|actor|external|module|class"}}
    ],
    "edges": [
        {{"from": "source_id", "to": "target_id", "label": "optional description"}}
    ]
}}

Rules:
- Only include elements actually present in the codebase
- Use snake_case for IDs, no spaces
- Keep it readable: 5-20 nodes ideally
- Identify communication patterns (REST, Kafka, DB queries, imports, etc.)

Return ONLY the JSON object.
"""
        try:
            bp_response = self._call_gpt(blueprint_prompt, temperature_override=0.3)
            blueprint = self._parse_json_response(bp_response)
        except Exception as e:
            blueprint = self._fallback_blueprint()

        # Update metadata
        blueprint.setdefault("nodes", [])
        blueprint.setdefault("edges", [])
        blueprint["metadata"] = {
            "node_count": len(blueprint["nodes"]),
            "edge_count": len(blueprint["edges"]),
        }

        # Step 2 — Generate Mermaid from blueprint
        diagram_code = self._blueprint_to_mermaid(blueprint, diagram_type)

        return {
            "diagram_type": diagram_type,
            "diagram": diagram_code,
            "description": blueprint.get("description", ""),
            "blueprint": blueprint,
        }

    # ------------------------------------------------------------------
    # Mermaid generation
    # ------------------------------------------------------------------

    def _blueprint_to_mermaid(self, blueprint: Dict, diagram_type: str) -> str:
        nodes = blueprint.get("nodes", [])
        edges = blueprint.get("edges", [])
        layout = blueprint.get("layout", "top-down")

        lines: List[str] = []

        if diagram_type == "SEQUENCE_DIAGRAM":
            lines.append("sequenceDiagram")
            for edge in edges:
                label = edge.get("label", "")
                lines.append(f"    {edge['from']}->>{edge['to']}: {label}")
            return "\n".join(lines)

        if diagram_type == "CLASS_DIAGRAM":
            lines.append("classDiagram")
            for node in nodes:
                lines.append(f"    class {node['id']} {{\n        {node['label']}\n    }}")
            for edge in edges:
                label = edge.get("label", "")
                lines.append(f"    {edge['from']} --> {edge['to']} : {label}")
            return "\n".join(lines)

        # Flowchart / Architecture / Data Flow
        if diagram_type == "FLOWCHART":
            orientation = "TD" if layout == "top-down" else "LR"
            lines.append(f"flowchart {orientation}")
        elif diagram_type == "DATA_FLOW_DIAGRAM":
            lines.append("graph LR")
        else:
            lines.append("graph TB")

        # Nodes with shape by type
        for node in nodes:
            nid = node["id"]
            label = node["label"]
            ntype = node.get("type", "component")

            if ntype == "database":
                lines.append(f"    {nid}[({label})]")
            elif ntype == "external":
                lines.append(f"    {nid}[/{label}/]")
            elif ntype == "actor":
                lines.append(f"    {nid}(({label}))")
            elif ntype in ("module", "class"):
                lines.append(f"    {nid}[{label}]")
            elif ntype == "service":
                lines.append(f"    {nid}[{label}]")
            else:
                lines.append(f"    {nid}[{label}]")

        # Edges
        for edge in edges:
            src = edge["from"]
            tgt = edge["to"]
            label = edge.get("label", "")
            if label:
                lines.append(f"    {src} -->|{label}| {tgt}")
            else:
                lines.append(f"    {src} --> {tgt}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helper – file tree
    # ------------------------------------------------------------------

    def _get_file_tree(self) -> str:
        paths = sorted(f["path"] for f in self.file_index)
        return "\n".join(paths)

    # ------------------------------------------------------------------
    # Helper – key snippets (for prompt context)
    # ------------------------------------------------------------------

    def _get_key_snippets(self, max_chars: int = 12000) -> str:
        """
        Return the most important file contents, capped at max_chars.
        Priority: config files, entry points, then alphabetical.
        """
        priority_names = {
            "main.py", "app.py", "index.js", "index.ts", "server.py",
            "server.js", "manage.py", "setup.py", "pyproject.toml",
            "package.json", "pom.xml", "build.gradle", "Cargo.toml",
            "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
            "requirements.txt", "go.mod", "Makefile", "README.md",
        }

        def sort_key(f: Dict) -> Tuple:
            basename = os.path.basename(f["path"])
            is_priority = basename in priority_names
            return (not is_priority, f["path"])

        sorted_files = sorted(self.file_index, key=sort_key)

        parts: List[str] = []
        total = 0
        for f in sorted_files:
            header = f"\n--- {f['path']} ({f['language']}) ---\n"
            chunk = header + f["content"]
            if total + len(chunk) > max_chars:
                remaining = max_chars - total
                if remaining > 200:
                    parts.append(header + f["content"][:remaining] + "\n...(truncated)")
                break
            parts.append(chunk)
            total += len(chunk)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helper – question context (relevant files)
    # ------------------------------------------------------------------

    def _build_question_context(self, question: str, max_chars: int = 14000) -> str:
        """Pick files most likely relevant to the question."""
        q_lower = question.lower()
        scored: List[Tuple[int, Dict]] = []

        for f in self.file_index:
            score = 0
            path_lower = f["path"].lower()
            content_lower = f["content"].lower()

            # Keywords from question appearing in path or content
            words = set(re.findall(r'\b\w{3,}\b', q_lower))
            for w in words:
                if w in path_lower:
                    score += 5
                if w in content_lower:
                    score += 1

            scored.append((score, f))

        # Sort by score descending, take top files
        scored.sort(key=lambda x: x[0], reverse=True)

        parts: List[str] = []
        total = 0
        for _score, f in scored:
            header = f"\n--- {f['path']} ---\n"
            chunk = header + f["content"]
            if total + len(chunk) > max_chars:
                remaining = max_chars - total
                if remaining > 200:
                    parts.append(header + f["content"][:remaining] + "\n...(truncated)")
                break
            parts.append(chunk)
            total += len(chunk)

        return "\n".join(parts) if parts else "(No relevant files found)"

    # ------------------------------------------------------------------
    # Fallback blueprint
    # ------------------------------------------------------------------

    def _fallback_blueprint(self) -> Dict[str, Any]:
        """Build a simple blueprint from the file tree when GPT fails."""
        # Group files by top-level directory
        modules: Dict[str, int] = {}
        for f in self.file_index:
            parts = f["path"].split(os.sep)
            module = parts[0] if len(parts) > 1 else "root"
            modules[module] = modules.get(module, 0) + 1

        nodes = []
        for mod in modules:
            nid = re.sub(r'[^a-zA-Z0-9_]', '_', mod).lower()
            nodes.append({"id": nid, "label": mod, "type": "module"})

        edges = []
        node_ids = [n["id"] for n in nodes]
        for i in range(len(node_ids) - 1):
            edges.append({"from": node_ids[i], "to": node_ids[i + 1], "label": ""})

        return {
            "diagram_type": "ARCHITECTURE_DIAGRAM",
            "title": "Project Modules",
            "description": "Fallback: top-level directory modules.",
            "granularity": "low",
            "layout": "top-down",
            "nodes": nodes,
            "edges": edges,
        }

    # ------------------------------------------------------------------
    # LLM call (OpenAI or Hugging Face)
    # ------------------------------------------------------------------

    def _call_gpt(
        self,
        prompt: str,
        temperature_override: Optional[float] = None,
    ) -> str:
        temp = temperature_override if temperature_override is not None else temperature

        if self.provider == "huggingface":
            return self._call_huggingface(prompt, temp)

        # Default: OpenAI
        response = self.client.chat.completions.create(
            model=openai_model_id,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_tokens,
            temperature=temp,
        )
        return response.choices[0].message.content

    def _call_huggingface(
        self,
        prompt: str,
        temp: float,
    ) -> str:
        """Call a Hugging Face Inference API model."""
        url = f"{hf_api_url.rstrip('/')}/{hf_model_id}"
        headers = {
            "Authorization": f"Bearer {hf_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temp,
                "return_full_text": False,
            },
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # HF Inference API returns a list of dicts with 'generated_text'
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "").strip()
        elif isinstance(data, dict):
            return data.get("generated_text", str(data)).strip()
        return str(data)

    # ------------------------------------------------------------------
    # JSON parser
    # ------------------------------------------------------------------

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        return json.loads(response)


# ---------------------------------------------------------------------------
# CLI usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = GitGPTAgent()

    # Point to current directory or any repo
    repo = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning repository: {repo}")
    stats = agent.load_repository(repo)
    print(f"Loaded {stats['total_files']} files")
    print(f"Languages: {stats['languages']}")
    print(f"\nSummary:\n{stats['summary']}")

    # Generate architecture diagram
    print("\n\nGenerating architecture diagram...")
    result = agent.generate_diagram("ARCHITECTURE_DIAGRAM")
    print(f"\n{result['diagram']}")

    # Ask a question
    print("\n\nAsking a question...")
    answer = agent.ask("What does this project do?")
    print(answer)
