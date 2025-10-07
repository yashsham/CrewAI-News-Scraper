# webui/streamlit_app.py
import streamlit as st
import subprocess
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]  # repo root (adjust if placed elsewhere)
REPORT_PATH = ROOT / "report.md"
AGENTS_YAML = ROOT / "src/ai_news/config/agents.yaml"
TASKS_YAML = ROOT / "src/ai_news/config/tasks.yaml"
ENV_PATH = ROOT / ".env"

st.set_page_config(page_title="CrewAI News Scraper", layout="wide")

st.title("📰 CrewAI News Scraper — Web UI")
st.write("Run your crew, edit agent/task configs, preview generated reports, and download outputs.")

# Sidebar: API key + controls
st.sidebar.header("Configuration")
openai_key = st.sidebar.text_input("OPENAI_API_KEY (paste here)", type="password", value=os.getenv("OPENAI_API_KEY", ""))
save_key = st.sidebar.checkbox("Save key to `.env` file (repo root)")

if save_key and openai_key:
    with open(ENV_PATH, "w") as f:
        f.write(f"OPENAI_API_KEY={openai_key}\n")
    st.sidebar.success("Saved to .env")

st.sidebar.markdown("---")
st.sidebar.header("Run Controls")
run_button = st.sidebar.button("▶️ Run CrewAI pipeline (`crewai run`)")

st.sidebar.markdown("**Notes:** `crewai` must be installed in the environment. See repo README for setup. :contentReference[oaicite:1]{index=1}")

# Show / edit YAML configs
st.header("Edit agent/tasks config")
col1, col2 = st.columns(2)

def read_file(path):
    if path.exists():
        return path.read_text()
    return ""

with col1:
    st.subheader("agents.yaml")
    agents_text = st.text_area("agents.yaml", value=read_file(AGENTS_YAML), height=350)
    if st.button("Save agents.yaml"):
        AGENTS_YAML.parent.mkdir(parents=True, exist_ok=True)
        AGENTS_YAML.write_text(agents_text)
        st.success("agents.yaml saved")

with col2:
    st.subheader("tasks.yaml")
    tasks_text = st.text_area("tasks.yaml", value=read_file(TASKS_YAML), height=350)
    if st.button("Save tasks.yaml"):
        TASKS_YAML.parent.mkdir(parents=True, exist_ok=True)
        TASKS_YAML.write_text(tasks_text)
        st.success("tasks.yaml saved")

# Runner: display logs
st.header("Run output / Logs")
log_container = st.empty()

if run_button:
    st.info("Starting CrewAI run — this may take a while depending on model calls.")
    # Build environment for subprocess
    env = os.environ.copy()
    if openai_key:
        env["OPENAI_API_KEY"] = openai_key

    # Run 'crewai run' in the repo root (same as README instructions). :contentReference[oaicite:2]{index=2}
    cmd = ["crewai", "run"]
    try:
        # Start the process and stream stdout
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True)

        output_lines = []
        with proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                output_lines.append(line)
                # update UI incrementally
                log_container.text_area("Logs (live)", value="".join(output_lines), height=300)
        proc.wait()
        if proc.returncode == 0:
            st.success("CrewAI run completed successfully.")
        else:
            st.error(f"CrewAI run returned non-zero exit code: {proc.returncode}")
    except FileNotFoundError:
        st.error("`crewai` CLI not found in environment. Install it or run this app in the same environment where crewai is installed.")
    except Exception as e:
        st.error(f"Error running crewai: {e}")

# Show generated report (if exists)
st.header("Generated report / outputs")
if REPORT_PATH.exists():
    st.markdown("### Report preview (report.md)")
    report_text = REPORT_PATH.read_text()
    st.code(report_text[:10000])  # show first 10k chars
    st.download_button("📥 Download report.md", data=report_text, file_name="report.md", mime="text/markdown")
else:
    st.info("No report.md found yet. Run the pipeline to generate one (it will usually appear in repo root).")

# Show list of output files (optional)
st.subheader("Files generated in repo root")
files = [p.name for p in ROOT.iterdir() if p.is_file() and p.name not in ("README.md", "LICENSE")]
st.write(files)
