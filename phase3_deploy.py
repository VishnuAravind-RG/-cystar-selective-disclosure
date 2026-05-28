import os, sys

print("=" * 60)
print("  CyStar - Phase 3: Docker + CI + Deploy Config")
print("=" * 60)
print()

if not (os.path.isdir("backend") and os.path.isdir("frontend")):
    print("ERROR: Run from project ROOT directory!")
    sys.exit(1)

def write_file(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  + {path}")

print("[1/9] Backend Dockerfile...")
write_file('backend/Dockerfile', 'FROM python:3.11-slim\n\nWORKDIR /app\n\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\nCOPY . .\n\nEXPOSE 8000\n\nCMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n')

print("[2/9] Frontend Dockerfile...")
write_file('frontend/Dockerfile', 'FROM node:20-alpine\n\nWORKDIR /app\n\nCOPY package*.json ./\nRUN npm ci\n\nCOPY . .\n\nARG NEXT_PUBLIC_API_URL=http://localhost:8000\nENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL\n\nRUN npm run build\n\nEXPOSE 3000\n\nCMD ["npm", "start"]\n')

print("[3/9] docker-compose.yml...")
write_file('docker-compose.yml', 'version: "3.8"\n\nservices:\n  backend:\n    build: ./backend\n    ports:\n      - "8000:8000"\n    env_file:\n      - ./backend/.env\n    restart: unless-stopped\n\n  frontend:\n    build:\n      context: ./frontend\n      args:\n        NEXT_PUBLIC_API_URL: http://localhost:8000\n    ports:\n      - "3000:3000"\n    depends_on:\n      - backend\n    restart: unless-stopped\n')

print("[4/9] GitHub Actions CI...")
write_file('.github/workflows/ci.yml', 'name: CI\n\non:\n  push:\n    branches: [main]\n  pull_request:\n    branches: [main]\n\njobs:\n  backend-test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Set up Python 3.11\n        uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n\n      - name: Install dependencies\n        run: |\n          cd backend\n          pip install -r requirements.txt\n\n      - name: Run tests\n        run: |\n          cd backend\n          pytest tests/test_sd_jwt.py -v\n        env:\n          MONGODB_URL: mongodb://localhost:27017\n          JWT_SECRET: test-secret-key-for-ci\n          DATABASE_NAME: cystar_test\n\n  frontend-lint:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Set up Node.js 20\n        uses: actions/setup-node@v4\n        with:\n          node-version: "20"\n\n      - name: Install dependencies\n        run: |\n          cd frontend\n          npm ci\n\n      - name: Lint\n        run: |\n          cd frontend\n          npm run lint\n')

print("[5/9] Render config...")
write_file('backend/render.yaml', 'services:\n  - type: web\n    name: cystar-backend\n    runtime: python\n    region: singapore\n    buildCommand: pip install -r requirements.txt\n    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT\n    envVars:\n      - key: MONGODB_URL\n        sync: false\n      - key: JWT_SECRET\n        sync: false\n      - key: DATABASE_NAME\n        value: cystar\n      - key: FRONTEND_URL\n        sync: false\n      - key: PYTHON_VERSION\n        value: 3.11.0\n')

print("[6/9] Vercel config...")
write_file('frontend/vercel.json', '{\n  "rewrites": [\n    { "source": "/(.*)", "destination": "/" }\n  ]\n}\n')

print("[7/9] Backend .env.example...")
write_file('backend/.env.example', '# MongoDB Atlas connection string\nMONGODB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority\n\n# Database name\nDATABASE_NAME=cystar\n\n# JWT Configuration\nJWT_SECRET=your-super-secret-key-change-this-in-production\nJWT_ALGORITHM=HS256\nJWT_EXPIRY_MINUTES=60\n\n# Frontend URL (for CORS)\nFRONTEND_URL=http://localhost:3000\n')

print("[8/9] Frontend .env.example...")
write_file('frontend/.env.example', '# Backend API URL\nNEXT_PUBLIC_API_URL=http://localhost:8000\n')

print("[9/9] Pinning bcrypt...")
req_path = 'backend/requirements.txt'
req = open(req_path, 'r').read()
if 'bcrypt==' not in req:
    req += 'bcrypt==4.0.1\n'
    open(req_path, 'w').write(req)
print('  + backend/requirements.txt (bcrypt pinned)')

print()
print("=" * 60)
print("  PHASE 3 COMPLETE!")
print("=" * 60)
