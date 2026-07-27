/**
 * PyMorph AI - Frontend Application Controller
 * Created By: Prabu Arvind M
 */

// Default Python Code Snippet (Initial display only)
const INITIAL_PYTHON_CODE = `# PyMorph AI - Multi-Language Python Code Converter
# Author: Prabu Arvind M

def fibonacci(n: int) -> list:
    """Generate a list containing the Fibonacci sequence up to n numbers."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    seq = [0, 1]
    while len(seq) < n:
        next_val = seq[-1] + seq[-2]
        seq.append(next_val)
    return seq

def main():
    terms = 10
    print(f"Generating first {terms} Fibonacci numbers:")
    result = fibonacci(terms)
    
    for idx, num in enumerate(result):
        print(f"Fibonacci[{idx}] = {num}")

if __name__ == "__main__":
    main()
`;

// Global State (Editors only, NO cached code!)
let pyEditor = null;
let targetEditor = null;
let currentTargetLang = "java";

// Settings State (Loaded from localStorage)
let aiProvider = localStorage.getItem("pymorph_provider") || "auto";
let userApiKey = (localStorage.getItem("pymorph_api_key") || "").trim();

// Helper to resolve absolute API URLs safely across all browsers
function getApiUrl(endpoint) {
    try {
        const origin = (window.location.origin || (window.location.protocol + "//" + window.location.host)).replace(/\/+$/, "");
        return origin + "/" + endpoint.replace(/^\/+/, "");
    } catch (e) {
        return "/" + endpoint.replace(/^\/+/, "");
    }
}

// Target Language Configuration Map for Monaco Editor
const LANG_MAP = {
    "java": { monacoId: "java", label: "Converted Code (Java)", icon: "fa-brands fa-java", ext: ".java" },
    "cpp": { monacoId: "cpp", label: "Converted Code (C++)", icon: "fa-solid fa-code", ext: ".cpp" },
    "c": { monacoId: "c", label: "Converted Code (C)", icon: "fa-solid fa-c", ext: ".c" },
    "embedded_c": { monacoId: "c", label: "Converted Code (Embedded C)", icon: "fa-microchip", ext: ".c" },
    "swift": { monacoId: "swift", label: "Converted Code (Swift)", icon: "fa-brands fa-swift", ext: ".swift" }
};

// Initialize Monaco Editors on Window Load
window.addEventListener("DOMContentLoaded", () => {
    require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs" } });

    require(["vs/editor/editor.main"], function () {
        // Initialize Left Monaco Editor (Python)
        pyEditor = monaco.editor.create(document.getElementById("pythonEditor"), {
            value: INITIAL_PYTHON_CODE,
            language: "python",
            theme: "vs-dark",
            automaticLayout: true,
            fontSize: 14,
            fontFamily: "JetBrains Mono",
            lineNumbers: "on",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            bracketPairColorization: { enabled: true },
            autoClosingBrackets: "always",
            tabSize: 4,
            padding: { top: 12, bottom: 12 }
        });

        // Initialize Right Monaco Editor (Target Language)
        targetEditor = monaco.editor.create(document.getElementById("convertedEditor"), {
            value: "// Click 'Convert Code' to generate target code using AI / Morpher Engine...\n",
            language: "java",
            theme: "vs-dark",
            automaticLayout: true,
            fontSize: 14,
            fontFamily: "JetBrains Mono",
            lineNumbers: "on",
            readOnly: false,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            bracketPairColorization: { enabled: true },
            tabSize: 4,
            padding: { top: 12, bottom: 12 }
        });

        // Update Line Counter on Change
        pyEditor.onDidChangeModelContent(() => {
            const count = pyEditor.getModel().getLineCount();
            document.getElementById("pyLinesCount").innerText = `${count} lines`;
        });

        // Setup Event Listeners
        setupEventListeners();
        loadSettingsUI();
    });
});

// Load Settings UI Elements
function loadSettingsUI() {
    document.getElementById("providerSelect").value = aiProvider;
    document.getElementById("customApiKey").value = userApiKey;
}

// Event Listeners Setup
function setupEventListeners() {
    // Run Python Code Button
    document.getElementById("runBtn").addEventListener("click", runPythonCode);

    // Run Converted Target Code Button
    document.getElementById("runTargetBtn").addEventListener("click", runTargetCode);

    // Convert Code Button
    document.getElementById("convertBtn").addEventListener("click", convertPythonCode);

    // Settings Modal Toggle
    document.getElementById("settingsBtn").addEventListener("click", () => {
        document.getElementById("settingsModal").classList.remove("hidden");
    });

    document.getElementById("closeModalBtn").addEventListener("click", () => {
        document.getElementById("settingsModal").classList.add("hidden");
    });

    document.getElementById("saveSettingsBtn").addEventListener("click", () => {
        aiProvider = document.getElementById("providerSelect").value;
        userApiKey = document.getElementById("customApiKey").value.trim();

        localStorage.setItem("pymorph_provider", aiProvider);
        localStorage.setItem("pymorph_api_key", userApiKey);

        document.getElementById("settingsModal").classList.add("hidden");
        showToast("AI Settings saved successfully!", "success");
    });

    // Target Language Selector Change
    document.getElementById("targetLangSelect").addEventListener("change", (e) => {
        currentTargetLang = e.target.value;
        const config = LANG_MAP[currentTargetLang] || LANG_MAP["java"];
        
        monaco.editor.setModelLanguage(targetEditor.getModel(), config.monacoId);
        document.getElementById("targetPaneTitle").innerText = config.label;
        
        const iconElem = document.getElementById("targetLangIcon");
        iconElem.className = `fa-solid ${config.icon} code-icon`;
    });

    // Copy Code Button
    document.getElementById("copyCodeBtn").addEventListener("click", copyConvertedCode);

    // Download Button
    document.getElementById("downloadBtn").addEventListener("click", downloadConvertedCode);

    // Save Python File Button
    document.getElementById("saveFileBtn").addEventListener("click", savePythonFile);

    // Open File Button
    document.getElementById("openFileBtn").addEventListener("click", () => {
        document.getElementById("fileInput").click();
    });

    document.getElementById("fileInput").addEventListener("change", handleFileOpen);

    // Clear Buttons
    document.getElementById("clearPyBtn").addEventListener("click", () => {
        pyEditor.setValue("");
        showToast("Python editor cleared", "info");
    });

    document.getElementById("clearConsoleBtn").addEventListener("click", () => {
        document.getElementById("consoleOutput").innerText = "";
        document.getElementById("consoleOutput").className = "console-pre";
        updateConsoleStatus("idle", 0);
    });

    // Collapse / Expand Console
    document.getElementById("toggleConsoleBtn").addEventListener("click", () => {
        const consolePanel = document.getElementById("consolePanel");
        consolePanel.classList.toggle("collapsed");
        const icon = document.getElementById("toggleConsoleBtn").querySelector("i");
        if (consolePanel.classList.contains("collapsed")) {
            icon.className = "fa-solid fa-chevron-up";
        } else {
            icon.className = "fa-solid fa-chevron-down";
        }
    });

    // Theme Toggle Button
    document.getElementById("themeToggleBtn").addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        
        const editorTheme = nextTheme === "dark" ? "vs-dark" : "vs";
        monaco.editor.setTheme(editorTheme);
        
        showToast(`Switched to ${nextTheme} theme`, "info");
    });
}

// Execute Python Code via Backend API
async function runPythonCode() {
    // ALWAYS read live contents from editor
    const pythonCode = pyEditor.getValue();
    if (!pythonCode.trim()) {
        showToast("Python code editor is empty!", "error");
        return;
    }

    const consoleOutput = document.getElementById("consoleOutput");
    const sourceTag = document.getElementById("consoleSourceTag");
    sourceTag.innerText = "Python";
    sourceTag.style.background = "rgba(0, 122, 204, 0.25)";
    sourceTag.style.borderColor = "rgba(0, 122, 204, 0.4)";

    consoleOutput.innerText = "Executing Python script...\n";
    consoleOutput.className = "console-pre";
    updateConsoleStatus("running", 0);

    try {
        const response = await fetch(getApiUrl("run"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: pythonCode })
        });

        const data = await response.json();

        if (data.success) {
            consoleOutput.innerText = data.stdout || "[Execution completed with no standard output]";
            consoleOutput.className = "console-pre";
            updateConsoleStatus("success", data.execution_time_ms);
            showToast("Python execution completed", "success");
        } else {
            const errText = data.stderr || data.error || "An execution error occurred.";
            consoleOutput.innerText = errText;
            consoleOutput.className = "console-pre error";
            updateConsoleStatus("error", data.execution_time_ms);
            showToast("Python execution failed", "error");
        }
    } catch (err) {
        consoleOutput.innerText = `Network/Server Error: ${err.message}`;
        consoleOutput.className = "console-pre error";
        updateConsoleStatus("error", 0);
        showToast("Failed to connect to backend server", "error");
    }
}

// Execute Converted Target Code via Backend API
async function runTargetCode() {
    const code = targetEditor.getValue();
    if (!code.trim() || code.startsWith("// Click 'Convert")) {
        showToast("Converted code pane is empty!", "error");
        return;
    }

    const langConfig = LANG_MAP[currentTargetLang] || LANG_MAP["java"];
    const consoleOutput = document.getElementById("consoleOutput");
    const sourceTag = document.getElementById("consoleSourceTag");
    
    sourceTag.innerText = langConfig.label.replace('Converted Code (', '').replace(')', '');
    sourceTag.style.background = "rgba(168, 85, 247, 0.25)";
    sourceTag.style.borderColor = "rgba(168, 85, 247, 0.4)";

    consoleOutput.innerText = `Compiling and executing ${sourceTag.innerText} code...\n`;
    consoleOutput.className = "console-pre";
    updateConsoleStatus("running", 0);

    try {
        const response = await fetch(getApiUrl("run-target"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: code,
                language: currentTargetLang
            })
        });

        const data = await response.json();

        if (data.success) {
            let outputText = data.stdout;
            if (data.toolchain) {
                outputText = `[Toolchain: ${data.toolchain}]\n----------------------------------------\n` + outputText;
            }
            consoleOutput.innerText = outputText || "[Program executed cleanly with no standard output]";
            consoleOutput.className = "console-pre";
            updateConsoleStatus("success", data.execution_time_ms);
            showToast(`${sourceTag.innerText} program executed successfully!`, "success");
        } else {
            const errText = data.stderr || data.error || "A compilation/execution error occurred.";
            consoleOutput.innerText = errText;
            consoleOutput.className = "console-pre error";
            updateConsoleStatus("error", data.execution_time_ms);
            showToast(`${sourceTag.innerText} execution failed`, "error");
        }
    } catch (err) {
        consoleOutput.innerText = `Server connection error: ${err.message}`;
        consoleOutput.className = "console-pre error";
        updateConsoleStatus("error", 0);
        showToast("Backend connection failed", "error");
    }
}

// Convert Python Code via Multi-Provider API / Dynamic Morpher Engine
async function convertPythonCode() {
    // ALWAYS read live contents from editor
    const pythonCode = pyEditor.getValue();
    
    console.log("Sending Python code:");
    console.log(pythonCode);

    if (!pythonCode.trim()) {
        showToast("Python code editor is empty!", "error");
        return;
    }

    const targetBadge = document.getElementById("aiStatusBadge");
    targetBadge.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Converting Code...`;
    
    showToast(`Converting Python to ${LANG_MAP[currentTargetLang].label.replace('Converted Code (', '').replace(')', '')}...`, "info");

    try {
        const cleanApiKey = (userApiKey && userApiKey.trim() !== "") ? userApiKey.trim() : null;
        const response = await fetch(getApiUrl("convert"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: pythonCode,
                target_language: currentTargetLang,
                provider: aiProvider,
                api_key: cleanApiKey
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            targetEditor.setValue(data.converted_code);
            const providerTag = data.provider || "AI Engine";
            targetBadge.innerHTML = `<i class="fa-solid fa-check"></i> ${providerTag} (${data.execution_time_ms} ms)`;
            showToast(`Converted via ${providerTag}!`, "success");
        } else {
            const errMsg = data.error || data.detail || "Failed to convert code.";
            targetEditor.setValue(`// Conversion Notification:\n// ${errMsg}`);
            targetBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Conversion Issue`;
            showToast(errMsg, "error");
        }
    } catch (err) {
        targetBadge.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Server Error`;
        showToast(`Server connection failed: ${err.message}`, "error");
    }
}

// Copy Converted Code to Clipboard
function copyConvertedCode() {
    const code = targetEditor.getValue();
    if (!code.trim()) {
        showToast("Converted code pane is empty!", "error");
        return;
    }

    navigator.clipboard.writeText(code).then(() => {
        showToast("Converted code copied to clipboard!", "success");
    }).catch(err => {
        showToast("Failed to copy code: " + err.message, "error");
    });
}

// Download Converted File
async function downloadConvertedCode() {
    const code = targetEditor.getValue();
    if (!code.trim()) {
        showToast("Nothing to download!", "error");
        return;
    }

    const config = LANG_MAP[currentTargetLang] || LANG_MAP["java"];
    const defaultName = `converted_${currentTargetLang}${config.ext}`;

    try {
        const response = await fetch(getApiUrl("download"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                code: code,
                language: currentTargetLang,
                filename: `pymorph_${currentTargetLang}`
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = defaultName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showToast(`Downloaded ${defaultName}`, "success");
        } else {
            showToast("Download failed.", "error");
        }
    } catch (err) {
        const blob = new Blob([code], { type: "text/plain" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = defaultName;
        a.click();
        window.URL.revokeObjectURL(url);
        showToast(`Downloaded ${defaultName}`, "success");
    }
}

// Save Python Code Local File
function savePythonFile() {
    const code = pyEditor.getValue();
    if (!code.trim()) {
        showToast("Python editor is empty!", "error");
        return;
    }

    const blob = new Blob([code], { type: "text/x-python" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "script.py";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("Saved script.py", "success");
}

// Handle Local File Upload (.py)
function handleFileOpen(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        pyEditor.setValue(e.target.result);
        showToast(`Opened file: ${file.name}`, "info");
    };
    reader.onerror = () => {
        showToast("Error reading file", "error");
    };
    reader.readAsText(file);
}

// Update Console Panel Status Indicator
function updateConsoleStatus(status, timeMs) {
    const statusElem = document.getElementById("execStatus");
    const timeElem = document.getElementById("execTime");

    statusElem.className = `status-indicator ${status}`;
    statusElem.innerText = status.toUpperCase();

    if (timeMs !== undefined && timeMs !== null) {
        timeElem.innerText = `${timeMs} ms`;
    }
}

// Notification Toast Popup Helper
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    let iconClass = "fa-circle-info";
    if (type === "success") iconClass = "fa-circle-check";
    if (type === "error") iconClass = "fa-circle-exclamation";

    toast.innerHTML = `<i class="fa-solid ${iconClass}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideIn 0.3s ease reverse forwards";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
