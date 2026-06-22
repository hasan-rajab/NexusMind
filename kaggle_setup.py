# ============================================================
# NexusMind — Kaggle Setup Script
# Run each cell block sequentially in a Kaggle notebook.
# ============================================================

# ── Cell 1: Install dependencies ────────────────────────────
# %pip install groq tavily-python chromadb sentence-transformers fastapi uvicorn[standard] pyngrok aiofiles python-multipart -q

# ── Cell 2: Clone repo & set path ───────────────────────────
# import subprocess, sys, os
# subprocess.run(["git", "clone", "https://github.com/hasan-rajab/nexusmind.git", "/kaggle/working/nexusmind"])
# os.chdir("/kaggle/working/nexusmind")
# sys.path.insert(0, "/kaggle/working/nexusmind")

# ── Cell 3: Set API keys from Kaggle Secrets ─────────────────
# from kaggle_secrets import UserSecretsClient
# secrets = UserSecretsClient()
# os.environ["GROQ_API_KEY"]   = secrets.get_secret("GROQ_API_KEY")
# os.environ["TAVILY_API_KEY"] = secrets.get_secret("TAVILY_API_KEY")
# os.environ["NGROK_TOKEN"]    = secrets.get_secret("NGROK_TOKEN")

# ── Cell 4: Start FastAPI in background thread ───────────────
# import threading, uvicorn
# from backend.app import app
# def run(): uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
# threading.Thread(target=run, daemon=True).start()
# print("Server started on port 8000")

# ── Cell 5: Start ngrok tunnel ───────────────────────────────
# from pyngrok import ngrok, conf
# conf.get_default().auth_token = os.environ["NGROK_TOKEN"]
# tunnel = ngrok.connect(8000)
# print(f"\n✅ NexusMind live at: {tunnel.public_url}\n")
