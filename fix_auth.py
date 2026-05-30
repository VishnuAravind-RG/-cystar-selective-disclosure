import os, sys, subprocess

if not (os.path.isdir("backend") and os.path.isdir("frontend")):
    print("ERROR: Run from project root!")
    sys.exit(1)

print("[1/4] Pulling frontend source from GitHub...")
r = subprocess.run(["git", "checkout", "origin/main", "--", "frontend/src/"], capture_output=True, text=True)
print(r.stdout or r.stderr or "Done")

layout_path = "frontend/src/app/(protected)/layout.tsx"

if not os.path.exists(layout_path):
    print(f"ERROR: {layout_path} not found!")
    sys.exit(1)

print("[2/4] Fixing auth guard race condition...")
code = open(layout_path, "r", encoding="utf-8").read()

old1 = 'if (!isLoading && !user) {\n      router.push("/login");\n    }'
new1 = 'if (!isLoading && !user) {\n      const token = localStorage.getItem("token");\n      if (!token) {\n        router.push("/login");\n      }\n    }'
code = code.replace(old1, new1)

old2 = 'if (!user) return null;'
new2 = 'if (!user && !localStorage.getItem("token")) return null;'
code = code.replace(old2, new2)

open(layout_path, "w", encoding="utf-8").write(code)
print("  Fixed: " + layout_path)

print("[3/4] Committing...")
for cmd in [
    ["git", "add", "."],
    ["git", "commit", "-m", "fix: auth guard race condition on share page"],
    ["git", "push", "origin", "main"],
]:
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip():
        print("  " + r.stdout.strip())
    if r.returncode != 0 and r.stderr.strip():
        print("  " + r.stderr.strip())

print()
print("[4/4] Done! Vercel will auto-redeploy.")
print("Try Share Selectively again after ~30 seconds.")
