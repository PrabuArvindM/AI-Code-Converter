---
title: PyMorph AI
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# PyMorph AI 🚀


> **AI-Powered Multi-Language Python Code Converter & Live Runner**  
> *Created By: Prabu Arvind M*

PyMorph AI is a production-ready, full-stack AI application that converts Python source code into multiple programming languages (**Java, C, C++, Embedded C, Swift**) using Google's Gemini API. It features a VS Code-inspired dark glassmorphism interface with dual Monaco Editors, an interactive console for live Python execution, and complete file management capabilities (Open, Save, Copy, Download).

---

## 🌟 Features

- **Online Monaco Editor**: Full VS Code editor integration with Python syntax highlighting, auto-completion, line numbers, bracket matching, and auto-indentation.
- **Live Python Execution**: Run Python scripts safely in a subprocess sandbox and view standard output (`stdout`), errors, and tracebacks (`stderr`) in real time with execution timings.
- **Multi-Language Conversion via Gemini AI**:
  - ☕ **Java** (`.java`)
  - ⚡ **C** (`.c`)
  - 🚀 **C++** (`.cpp`)
  - 🔌 **Embedded C** (`.c` for microcontrollers)
  - 🍎 **Swift** (`.swift`)
- **Strict Logic & Code Preservation**: Tailored prompts instruct Gemini AI to retain original variable names, function names, comments, logic, and algorithms while producing idiomatic, compilable code.
- **File Management**:
  - **Open File**: Upload and edit local `.py` scripts.
  - **Save File**: Save Python scripts to `.py`.
  - **Download**: One-click download generated target code (`.java`, `.cpp`, `.c`, `.swift`).
  - **Copy to Clipboard**: Instant clipboard copy with notification toast.
- **Modern VS Code UI**: Dark glassmorphism layout, responsive dual-pane editor, theme switcher, collapsible console, and notification toasts.

---

## 🏗️ Project Structure

```
PyMorphAI/
├── backend/
│   ├── app.py           # FastAPI web server and routes (/run, /convert, /download)
│   ├── converter.py     # Google Gemini API integration and code translation engine
│   ├── runner.py        # Secure Python execution sandbox with timeout limits
│   ├── prompts.py       # Prompt engineering for target languages
│   ├── utils.py         # File utilities, language metadata, and sanitization
│   ├── config.py        # Settings loader with Pydantic & dotenv
│   ├── requirements.txt # Python dependencies
│   ├── .env.example     # Environment variable template
│   └── .env             # Local environment secrets
├── frontend/
│   ├── index.html       # Single Page Application HTML structure
│   ├── style.css        # VS Code Glassmorphism CSS design system
│   └── script.js        # Monaco Editor initialization & frontend controller
├── uploads/             # Temporary directory for script execution
├── outputs/             # Converted files storage
├── README.md            # Complete application documentation
├── LICENSE              # MIT License
└── .gitignore           # Git ignore rules
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI**: Modern, high-performance web framework.
- **Uvicorn**: Lightning-fast ASGI server.
- **Google Gemini API (`google-genai` / `google-generativeai`)**: Code conversion model.
- **Pydantic Settings & python-dotenv**: Environment configuration.

### Frontend
- **HTML5 & CSS3**: Custom glassmorphism variables, flexbox/grid, animated notifications.
- **Vanilla JavaScript (ES6+)**: Async fetch calls, event handling.
- **Monaco Editor**: Official VS Code editor component.
- **FontAwesome 6**: Modern iconography.

---

## 🔑 Obtaining a Google Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Create API Key**.
4. Copy the generated API key string.

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/PyMorphAI.git
cd PyMorphAI
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` inside the `backend` folder and add your Gemini API key:
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and update:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
PORT=8000
HOST=0.0.0.0
MAX_EXECUTION_TIMEOUT=5
```

### 3. Install Backend Dependencies
Create a virtual environment and install required packages:
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 4. Run the Backend Server
Start Uvicorn server:
```bash
python3 -m backend.app
# OR
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```
The server will start at: `http://localhost:8000`

### 5. Access the Web Application
Open your web browser and navigate to:
```
http://localhost:8000
```

---

## 📡 API Endpoints

### 1. `POST /run`
Executes Python code safely.
- **Request Body**:
  ```json
  {
    "code": "print('Hello PyMorph AI')"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "stdout": "Hello PyMorph AI\n",
    "stderr": "",
    "execution_time_ms": 42.15,
    "exit_code": 0
  }
  ```

### 2. `POST /convert`
Converts Python code into target programming language using Gemini API.
- **Request Body**:
  ```json
  {
    "code": "def add(a, b):\n    return a + b",
    "target_language": "java"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "converted_code": "public class Main {\n    public static int add(int a, int b) {\n        return a + b;\n    }\n}",
    "target_language": "Java",
    "execution_time_ms": 1240.5
  }
  ```

### 3. `POST /download`
Streams target code as a downloadable file attachment.
- **Request Body**:
  ```json
  {
    "code": "public class Main { ... }",
    "language": "java",
    "filename": "Main"
  }
  ```

### 4. `GET /health`
Returns system status and API configuration state.

---

## 🖼️ Application Preview

```
+-----------------------------------------------------------------------------------+
|  PyMorph AI  | Created By: Prabu Arvind M                    [Theme] [GitHub]    |
+-----------------------------------------------------------------------------------+
|  [> Run]  [Open] [Save]  |  Target: [ Java (v) ]  [* Convert]  |  [Copy] [Download]|
+--------------------------------------------------+--------------------------------+
|  Python Source Editor (Monaco)                   | Converted Code (Java Monaco)   |
|  -----------------------------                   | ----------------------------   |
|  1  def main():                                  | 1  public class Main {         |
|  2      print("Hello World")                     | 2      public static void main |
|  3                                               | 3          System.out.println  |
+--------------------------------------------------+--------------------------------+
|  Terminal Output [SUCCESS] [42 ms]                                                |
|  Hello World                                                                      |
+-----------------------------------------------------------------------------------+
```

---

## 🔭 Future Scope

- **Additional Languages**: Rust, Go, TypeScript, C#, and Kotlin conversion support.
- **AST-Assisted Verification**: Combine Gemini AI with language AST validators to ensure syntax correctness before displaying output.
- **Docker Container Sandbox**: Upgrade Python execution runner to isolated Docker containers for memory/network isolation.
- **Multi-File Workspace Support**: Convert entire Python packages or projects with directory trees.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

*Created with ❤️ by **Prabu Arvind M***
