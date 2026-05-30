import os, sys, subprocess
from pathlib import Path

ROOT = Path.cwd()
if not (ROOT / "backend").is_dir() or not (ROOT / "frontend").is_dir():
    print("ERROR: Run from project root: cystar-selective-disclosure")
    sys.exit(1)

print("Fixing auth guard and removing IITM/Summer Internship wording...")

# Restore frontend source from GitHub if local files are missing
layout_path = ROOT / "frontend" / "src" / "app" / "(protected)" / "layout.tsx"
if not layout_path.exists():
    print("frontend/src missing locally; restoring from origin/main...")
    subprocess.run(["git", "fetch", "origin", "main"], check=False)
    subprocess.run(["git", "checkout", "origin/main", "--", "frontend/src/"], check=False)

if not layout_path.exists():
    print("ERROR: frontend/src/app/(protected)/layout.tsx not found")
    sys.exit(1)

# Patch auth guard
code = layout_path.read_text(encoding="utf-8")
code = code.replace('if (!isLoading && !user) {\n      router.push("/login");\n    }', 'if (!isLoading && !user) {\n      const token = localStorage.getItem("token");\n      if (!token) {\n        router.push("/login");\n      }\n    }')
code = code.replace('if (!user) return null;', 'if (!user && !localStorage.getItem("token")) return null;')
layout_path.write_text(code, encoding="utf-8")
print("patched protected layout")

# Remove IITM / Summer Internship wording from frontend source
frontend_src = ROOT / "frontend" / "src"
replacements = {'CyStar Summer Internship Assessment — IIT Madras': 'CyStar Selective Disclosure Platform', 'CyStar Summer Internship Assessment - IIT Madras': 'CyStar Selective Disclosure Platform', 'Built for CyStar — IIT Madras': 'Built for secure credential sharing', 'Built for CyStar - IIT Madras': 'Built for secure credential sharing', 'CyStar Selective Disclosure & Verification — IIT Madras': 'CyStar Selective Disclosure & Verification', 'CyStar Selective Disclosure & Verification - IIT Madras': 'CyStar Selective Disclosure & Verification', 'IIT Madras': '', 'IITM': '', 'Summer Internship': ''}
changed = []
for ext in ("*.tsx", "*.ts"):
    for path in frontend_src.rglob(ext):
        text = path.read_text(encoding="utf-8")
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))
print("cleaned files:", changed if changed else "none")

# Ensure API fallback uses deployed backend
api_client = ROOT / "frontend" / "src" / "lib" / "api-client.ts"
if api_client.exists():
    api = api_client.read_text(encoding="utf-8")
    api = api.replace('process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"', 'process.env.NEXT_PUBLIC_API_URL || "https://cystar-selective-disclosure.onrender.com"')
    api = api.replace('process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001"', 'process.env.NEXT_PUBLIC_API_URL || "https://cystar-selective-disclosure.onrender.com"')
    api_client.write_text(api, encoding="utf-8")
    print("checked api-client fallback")

# Commit and push
commands = [
    ["git", "add", "frontend/src"],
    ["git", "commit", "-m", "fix: share auth guard and remove internship wording"],
    ["git", "push", "origin", "main"],
]
for cmd in commands:
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.returncode != 0:
        if r.stderr.strip(): print(r.stderr.strip())
        if "nothing to commit" not in (r.stdout + r.stderr).lower():
            sys.exit(r.returncode)
print("DONE. Vercel will auto-redeploy. Logout/login once, then test Share Selectively.")