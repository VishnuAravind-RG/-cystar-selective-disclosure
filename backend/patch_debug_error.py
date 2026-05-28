from pathlib import Path

p = Path("app/main.py")
code = p.read_text(encoding="utf-8")

if "debug_global_exception_handler" not in code:
    code = code.replace(
        "from fastapi import FastAPI",
        "from fastapi import FastAPI, Request"
    )

    code = code.replace(
        "from fastapi.middleware.cors import CORSMiddleware",
        "from fastapi.middleware.cors import CORSMiddleware\nfrom fastapi.responses import JSONResponse\nimport traceback"
    )

    insert = '''

@app.exception_handler(Exception)
async def debug_global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": traceback.format_exc(),
        },
    )
'''
    code = code + insert

p.write_text(code, encoding="utf-8")
print("Patched main.py with debug exception handler")
