"""
PyMorph AI FastAPI Backend Server.
Provides API endpoints for Python code execution, Multi-Provider AI code conversion, target language code execution, and file download.
Created By: Prabu Arvind M
"""

import os
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings, BASE_DIR
from backend.runner import execute_python_code, execute_target_code
from backend.converter import convert_code
from backend.utils import get_language_info, sanitize_filename

# Initialize FastAPI Application
app = FastAPI(
    title="PyMorph AI",
    description="Production AI code converter and multi-language execution platform by Prabu Arvind M",
    version="1.3.0"
)

# Enable CORS for local development and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files path
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Pydantic Schemas for API Requests
class CodeRunRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    inputs: Optional[str] = Field("", description="Optional stdin input values")

class CodeRunTargetRequest(BaseModel):
    code: str = Field(..., description="Converted target code to execute")
    language: str = Field(..., description="Target language (java, c, cpp, embedded_c, swift)")
    inputs: Optional[str] = Field("", description="Optional stdin input values")


class CodeConvertRequest(BaseModel):
    code: str = Field(..., description="Python source code to convert")
    target_language: str = Field(..., description="Target language (java, c, cpp, embedded_c, swift)")
    provider: Optional[str] = Field("auto", description="AI Provider choice (auto, openrouter, groq, gemini, offline)")
    api_key: Optional[str] = Field(None, description="Optional custom API key provided by user")

class CodeDownloadRequest(BaseModel):
    code: str = Field(..., description="Code content to download")
    language: str = Field(..., description="Language identifier")
    filename: str = Field("code", description="Base filename without extension")


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": f"Internal Server Error: {str(exc)}"}
    )


# API Routes
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """
    Serves the PyMorph AI frontend single-page application.
    """
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>PyMorph AI API Server is Running</h1><p>Frontend file index.html not found.</p>")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for status monitoring.
    """
    return {
        "status": "online",
        "app": "PyMorph AI",
        "author": "Prabu Arvind M",
        "gemini_api_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "openrouter_configured": bool(settings.OPENROUTER_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY)
    }


@app.post("/run")
async def run_python_code(payload: CodeRunRequest):
    """
    Executes Python source code securely and returns standard output/error.
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Python code cannot be empty.")

    result = await execute_python_code(payload.code, inputs=payload.inputs)
    return result


@app.post("/run-target")
async def run_target_program(payload: CodeRunTargetRequest):
    """
    Compiles and executes converted target code (Java, C, C++, Embedded C, Swift).
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Converted target code cannot be empty.")
    if not payload.language.strip():
        raise HTTPException(status_code=400, detail="Target language must be specified.")

    result = await execute_target_code(payload.code, payload.language, inputs=payload.inputs)
    return result


@app.post("/convert")
async def convert_python_code(payload: CodeConvertRequest):
    """
    Converts Python code into target programming language using AI or Morpher engine.
    """
    print("Received code:")
    print(payload.code)

    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Python code cannot be empty.")
    
    if not payload.target_language.strip():
        raise HTTPException(status_code=400, detail="Target language must be specified.")

    result = await convert_code(
        python_code=payload.code, 
        target_language=payload.target_language,
        provider=payload.provider,
        custom_api_key=payload.api_key
    )
    
    return result


@app.post("/download")
async def download_converted_file(payload: CodeDownloadRequest):
    """
    Generates and returns downloadable code file with correct extension and headers.
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code content cannot be empty.")

    lang_info = get_language_info(payload.language)
    safe_base = sanitize_filename(payload.filename) or "code"
    
    if safe_base.endswith(lang_info["extension"]):
        safe_base = safe_base[:-len(lang_info["extension"])]
        
    full_filename = f"{safe_base}{lang_info['extension']}"
    
    return Response(
        content=payload.code,
        media_type=lang_info["mime"],
        headers={
            "Content-Disposition": f'attachment; filename="{full_filename}"'
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=settings.HOST, port=settings.PORT, reload=True)
