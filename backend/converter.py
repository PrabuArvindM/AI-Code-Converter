"""
Multi-Provider Code Conversion Engine for PyMorph AI.
Supports Gemini, OpenRouter (Free Open-Source Models), Groq, and a Dynamic Offline Morpher fallback.
Created By: Prabu Arvind M
"""

import re
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from backend.config import settings
from backend.prompts import SYSTEM_INSTRUCTION, get_conversion_prompt
from backend.utils import clean_markdown_code_blocks, get_language_info


def convert_offline_fallback(python_code: str, target_language: str) -> str:
    """
    Built-in dynamic rule-based Python transpiler fallback.
    Converts incoming Python code dynamically line-by-line without any hardcoded sample code.
    """
    lang_key = target_language.lower().strip().replace(" ", "_")
    lines = python_code.splitlines()

    class_methods = []
    main_lines = []
    
    indent_stack = []
    in_docstring = False
    current_func = None
    current_lines = main_lines

    for line in lines:
        raw_indent = line[:len(line) - len(line.lstrip())]
        indent_level = len(raw_indent)
        stripped = line.strip()

        # Handle docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            cleaned_doc = stripped.strip('"\'- ').strip()
            if cleaned_doc:
                current_lines.append(f"{raw_indent}// {cleaned_doc}")
            is_single_line = (stripped.startswith('"""') and stripped.endswith('"""') and len(stripped) > 3) or \
                             (stripped.startswith("'''") and stripped.endswith("'''") and len(stripped) > 3)
            if not is_single_line:
                in_docstring = not in_docstring
            continue
            
        if in_docstring:
            if stripped.endswith('"""') or stripped.endswith("'''"):
                in_docstring = False
            else:
                current_lines.append(f"{raw_indent}// {stripped}")
            continue

        # Empty lines
        if not stripped:
            current_lines.append("")
            continue

        # Comments
        if stripped.startswith("#"):
            current_lines.append(f"{raw_indent}// {stripped[1:].strip()}")
            continue

        # Strip Python main guard & recursive main() invocation
        if "if __name__ ==" in stripped or "if __name__==" in stripped or stripped in ["main()", "main();"]:
            continue


        is_elif_else = stripped.startswith("elif ") or stripped == "else:" or stripped.startswith("else:")
        # Pop indent stack and append closing braces
        while indent_stack and (indent_level < indent_stack[-1][0] or (indent_level == indent_stack[-1][0] and not is_elif_else)):
            lvl, brace_indent = indent_stack.pop()
            current_lines.append(f"{brace_indent}}}")

        # Check if function definition ended
        if current_func and indent_level <= current_func["indent"]:
            current_func = None
            current_lines = main_lines

        # Function Definitions: `def name(params):`
        func_match = re.match(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\((.*?)\)(?:\s*->\s*(.*?))?:", stripped)
        if func_match:
            name, params, ret_type = func_match.groups()
            param_list = params.split(",") if params.strip() else []
            formatted_params = []
            
            for p in param_list:
                p = p.strip()
                if ":" in p:
                    pname, ptype = p.split(":", 1)
                    pname, ptype = pname.strip(), ptype.strip()
                    if lang_key in ["swift"]:
                        formatted_params.append(f"{pname}: {ptype.capitalize()}")
                    else:
                        c_type = "int" if "int" in ptype.lower() else "String"
                        formatted_params.append(f"{c_type} {pname}")
                else:
                    if lang_key in ["swift"]:
                        formatted_params.append(f"{p}: Any")
                    else:
                        formatted_params.append(f"int {p}")

            params_str = ", ".join(formatted_params)

            if name == "main":
                continue

            current_func = {"name": name, "indent": indent_level}
            current_lines = class_methods
            indent_stack.append((indent_level, raw_indent))

            if lang_key == "java":
                ret = "List<Integer>" if ret_type and "list" in ret_type.lower() else ("int" if ret_type and "int" in ret_type.lower() else "void")
                current_lines.append(f"{raw_indent}public static {ret} {name}({params_str}) {{")
            elif lang_key == "cpp":
                ret = "std::vector<int>" if ret_type and "list" in ret_type.lower() else ("int" if ret_type and "int" in ret_type.lower() else "void")
                current_lines.append(f"{raw_indent}{ret} {name}({params_str}) {{")
            elif lang_key in ["c", "embedded_c"]:
                ret = "int" if ret_type and "int" in ret_type.lower() else "void"
                current_lines.append(f"{raw_indent}{ret} {name}({params_str}) {{")
            elif lang_key == "swift":
                ret_str = " -> [Int]" if ret_type and "list" in ret_type.lower() else (f" -> {ret_type.strip()}" if ret_type else "")
                current_lines.append(f"{raw_indent}func {name}({params_str}){ret_str} {{")
            continue

        # Conditionals (if, elif, else)
        if stripped.startswith("if ") and stripped.endswith(":"):
            cond = stripped[3:-1].strip()
            indent_stack.append((indent_level, raw_indent))
            current_lines.append(f"{raw_indent}if ({cond}) {{")
            continue
        elif stripped.startswith("elif ") and stripped.endswith(":"):
            cond = stripped[5:-1].strip()
            current_lines.append(f"{raw_indent}}} else if ({cond}) {{")
            continue
        elif stripped == "else:":
            current_lines.append(f"{raw_indent}}} else {{")
            continue

        # Loops
        if stripped.startswith("while ") and stripped.endswith(":"):
            cond = stripped[6:-1].strip()
            if lang_key == "swift":
                cond = re.sub(r"len\(([a-zA-Z0-9_]+)\)", r"\1.count", cond)
            else:
                cond = re.sub(r"len\(([a-zA-Z0-9_]+)\)", r"\1.size()", cond)
            indent_stack.append((indent_level, raw_indent))
            current_lines.append(f"{raw_indent}while ({cond}) {{")
            continue


        enum_match = re.match(r"^for\s+([a-zA-Z0-9_]+),\s*([a-zA-Z0-9_]+)\s+in\s+enumerate\(([a-zA-Z0-9_]+)\):", stripped)
        if enum_match:
            idx_var, val_var, list_var = enum_match.groups()
            indent_stack.append((indent_level, raw_indent))
            if lang_key == "java":
                current_lines.append(f"{raw_indent}for (int {idx_var} = 0; {idx_var} < {list_var}.size(); {idx_var}++) {{")
                current_lines.append(f"{raw_indent}    int {val_var} = {list_var}.get({idx_var});")
            elif lang_key == "cpp":
                current_lines.append(f"{raw_indent}for (size_t {idx_var} = 0; {idx_var} < {list_var}.size(); {idx_var}++) {{")
                current_lines.append(f"{raw_indent}    auto {val_var} = {list_var}[{idx_var}];")
            elif lang_key == "swift":
                current_lines.append(f"{raw_indent}for ({idx_var}, {val_var}) in {list_var}.enumerated() {{")
            else:
                current_lines.append(f"{raw_indent}for (int {idx_var} = 0; {idx_var} < 10; {idx_var}++) {{")
            continue

        range_match = re.match(r"^for\s+([a-zA-Z0-9_]+)\s+in\s+range\((.*?)\):", stripped)
        if range_match:
            var_name, rng = range_match.groups()
            indent_stack.append((indent_level, raw_indent))
            if lang_key in ["java", "cpp", "c", "embedded_c"]:
                current_lines.append(f"{raw_indent}for (int {var_name} = 0; {var_name} < {rng}; {var_name}++) {{")
            elif lang_key == "swift":
                current_lines.append(f"{raw_indent}for {var_name} in 0..<{rng} {{")
            continue

        # Return Statements
        if stripped.startswith("return"):
            val = stripped[6:].strip()
            if val == "[]":
                if lang_key == "java": val = "new ArrayList<>()"
                elif lang_key == "cpp": val = "{}"
                elif lang_key == "swift": val = "[]"
            elif val == "[0]":
                if lang_key == "java": val = "new ArrayList<>(Arrays.asList(0))"
                elif lang_key == "cpp": val = "{0}"
                elif lang_key == "swift": val = "[0]"
            
            suffix = ";" if lang_key in ["java", "cpp", "c", "embedded_c"] else ""
            current_lines.append(f"{raw_indent}return {val}{suffix}")
            continue

        # Print Statements
        if stripped.startswith("print(") and stripped.endswith(")"):
            inner = stripped[6:-1].strip()
            if inner.startswith("f\"") or inner.startswith("f'"):
                raw_str = inner[2:-1]
                if lang_key == "java":
                    java_str = re.sub(r"\{([a-zA-Z0-9_\+\-\*\/\s\[\]]+)\}", r'" + (\1) + "', raw_str)
                    current_lines.append(f'{raw_indent}System.out.println("{java_str}");')
                elif lang_key == "cpp":
                    cpp_parts = re.split(r"\{([a-zA-Z0-9_\+\-\*\/\s\[\]]+)\}", raw_str)
                    cpp_str = " << ".join([f'"{p}"' if idx % 2 == 0 else f'({p})' for idx, p in enumerate(cpp_parts) if p])
                    current_lines.append(f'{raw_indent}std::cout << {cpp_str} << std::endl;')
                elif lang_key in ["c", "embedded_c"]:
                    c_str = re.sub(r"\{([a-zA-Z0-9_\+\-\*\/\s\[\]]+)\}", r"%d", raw_str)
                    vars_found = re.findall(r"\{([a-zA-Z0-9_\+\-\*\/\s\[\]]+)\}", raw_str)
                    vars_str = ", ".join(vars_found)
                    vars_prefix = f", {vars_str}" if vars_str else ""
                    current_lines.append(f'{raw_indent}printf("{c_str}\\n"{vars_prefix});')
                elif lang_key == "swift":
                    swift_str = re.sub(r"\{([a-zA-Z0-9_\+\-\*\/\s\[\]]+)\}", r"\\(\1)", raw_str)
                    current_lines.append(f'{raw_indent}print("{swift_str}")')
                continue
            else:
                if lang_key == "java":
                    current_lines.append(f'{raw_indent}System.out.println({inner});')
                elif lang_key == "cpp":
                    current_lines.append(f'{raw_indent}std::cout << {inner} << std::endl;')
                elif lang_key in ["c", "embedded_c"]:
                    if inner.startswith('"') or inner.startswith("'"):
                        current_lines.append(f'{raw_indent}printf("%s\\n", {inner});')
                    else:
                        current_lines.append(f'{raw_indent}printf("%d\\n", {inner});')
                elif lang_key == "swift":
                    current_lines.append(f'{raw_indent}print({inner})')
                continue

        # Variable Assignments & Declarations
        if "=" in stripped and not stripped.startswith("if") and not stripped.startswith("while"):
            var_name, val = [x.strip() for x in stripped.split("=", 1)]
            
            if val == "[0, 1]":
                if lang_key == "java":
                    current_lines.append(f"{raw_indent}List<Integer> {var_name} = new ArrayList<>(Arrays.asList(0, 1));")
                elif lang_key == "cpp":
                    current_lines.append(f"{raw_indent}std::vector<int> {var_name} = {{0, 1}};")
                elif lang_key == "swift":
                    current_lines.append(f"{raw_indent}var {var_name} = [0, 1]")
                continue

            val = re.sub(r"([a-zA-Z0-9_]+)\[-1\]", r"\1.get(\1.size() - 1)", val) if lang_key == "java" else val
            val = re.sub(r"([a-zA-Z0-9_]+)\[-2\]", r"\1.get(\1.size() - 2)", val) if lang_key == "java" else val
            val = re.sub(r"([a-zA-Z0-9_]+)\[-1\]", r"\1.back()", val) if lang_key == "cpp" else val
            val = re.sub(r"([a-zA-Z0-9_]+)\[-2\]", r"\1[\1.size() - 2]", val) if lang_key == "cpp" else val

            if lang_key == "java":
                type_prefix = "int " if (val.isdigit() or "+" in val or "-" in val or "*" in val) else "var "
                current_lines.append(f"{raw_indent}{type_prefix}{var_name} = {val};")
            elif lang_key in ["cpp", "c", "embedded_c"]:
                type_prefix = "auto " if lang_key == "cpp" else "int "
                current_lines.append(f"{raw_indent}{type_prefix}{var_name} = {val};")
            elif lang_key == "swift":
                current_lines.append(f"{raw_indent}var {var_name} = {val}")
            continue

        # List Method: seq.append(next_val)
        if ".append(" in stripped:
            if lang_key == "java":
                current_lines.append(f"{raw_indent}" + stripped.replace(".append(", ".add(").rstrip(";") + ";")
            elif lang_key == "cpp":
                current_lines.append(f"{raw_indent}" + stripped.replace(".append(", ".push_back(").rstrip(";") + ";")
            elif lang_key == "swift":
                current_lines.append(f"{raw_indent}" + stripped.rstrip(";"))
            continue

        # Default statements
        if lang_key in ["java", "cpp", "c", "embedded_c"]:
            suffix = ";" if not stripped.endswith(";") and not stripped.endswith("}") and not stripped.endswith("{") else ""
            current_lines.append(f"{raw_indent}{stripped}{suffix}")
        else:
            current_lines.append(f"{raw_indent}{stripped}")

    if lang_key in ["cpp", "c", "embedded_c"]:
        main_lines.append("return 0;")

    # Close remaining indent stack
    while indent_stack:
        lvl, brace_indent = indent_stack.pop()
        current_lines.append(f"{brace_indent}}}")

    class_code = "\n".join(class_methods)
    main_code = "\n".join(main_lines)
    body_code = "\n".join(class_methods + main_lines)
    indented_body = "\n".join(["    " + l if l.strip() else "" for l in body_code.splitlines()])

    # Wrap body code dynamically in clean main class structure
    if lang_key == "java":
        indented_methods = "\n".join(["    " + l if l.strip() else "" for l in class_code.splitlines()])
        indented_main = "\n".join(["        " + l if l.strip() else "" for l in main_code.splitlines()])
        
        methods_block = (indented_methods + "\n\n") if indented_methods.strip() else ""
        return f"""// Converted from Python to Java (PyMorph Morpher Engine)
import java.util.*;

public class Main {{
{methods_block}    public static void main(String[] args) {{
{indented_main}
    }}
}}"""

    elif lang_key == "cpp":
        indented_methods = "\n".join(["" + l if l.strip() else "" for l in class_code.splitlines()])
        indented_main = "\n".join(["    " + l if l.strip() else "" for l in main_code.splitlines()])
        
        methods_block = (indented_methods + "\n\n") if indented_methods.strip() else ""
        return f"""// Converted from Python to C++ (PyMorph Morpher Engine)
#include <iostream>
#include <vector>
#include <string>

{methods_block}int main() {{
{indented_main}
}}"""

    elif lang_key in ["c", "embedded_c"]:
        indented_methods = "\n".join(["" + l if l.strip() else "" for l in class_code.splitlines()])
        indented_main = "\n".join(["    " + l if l.strip() else "" for l in main_code.splitlines()])
        
        methods_block = (indented_methods + "\n\n") if indented_methods.strip() else ""
        return f"""/* Converted from Python to {target_language} (PyMorph Morpher Engine) */
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

{methods_block}int main(void) {{
{indented_main}
}}"""



    elif lang_key == "swift":
        return f"""// Converted from Python to Swift (PyMorph Morpher Engine)
import Foundation

{body_code}"""

    return body_code



def convert_with_openrouter(python_code: str, target_language: str, api_key: str) -> Optional[str]:
    """
    Calls OpenRouter API using free open-source models (Qwen 2.5 Coder / Llama 3.3 / DeepSeek).
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = get_conversion_prompt(python_code, target_language)

    models = [
        "qwen/qwen-2.5-coder-32b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free"
    ]

    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://pymorphai.org",
            "X-Title": "PyMorph AI"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status == 200:
                    res_data = json.loads(response.read().decode("utf-8"))
                    choices = res_data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"]["content"]
        except Exception:
            continue

    return None


def convert_with_groq(python_code: str, target_language: str, api_key: str) -> Optional[str]:
    """
    Calls Groq API with Llama 3.3 model.
    """
    if not api_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    prompt = get_conversion_prompt(python_code, target_language)
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"]["content"]
    except Exception:
        pass

    return None


async def convert_with_gemini(python_code: str, target_language: str, api_key: str) -> Optional[str]:
    """
    Calls Google Gemini API.
    """
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    user_prompt = get_conversion_prompt(python_code, target_language)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        for model in ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"]:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                    )
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[google.genai Error for {model}]:", e)
                continue

    except Exception as exc:
        print("[google.genai Client Error]:", exc)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        for model_name in ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-pro"]:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                response = model.generate_content(user_prompt, generation_config={"temperature": 0.1})
                if response and response.text:
                    return response.text
            except Exception as e:
                print(f"[google.generativeai Error for {model_name}]:", e)
                continue
    except Exception as exc:
        print("[google.generativeai Client Error]:", exc)

    return None



async def convert_code(
    python_code: str, 
    target_language: str, 
    provider: Optional[str] = "auto",
    custom_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main code conversion coordinator.
    Supports OpenRouter Free, Groq, Gemini, and Zero-API Key Offline Morpher.
    """
    start_time = time.perf_counter()

    if not python_code or not python_code.strip():
        return {
            "success": False,
            "error": "Python source code cannot be empty.",
            "converted_code": "",
            "target_language": target_language,
            "execution_time_ms": 0
        }

    lang_info = get_language_info(target_language)
    provider_used = "Offline Morpher"
    converted_code = None

    gemini_key = custom_api_key or settings.GEMINI_API_KEY
    openrouter_key = custom_api_key or settings.OPENROUTER_API_KEY
    groq_key = custom_api_key or settings.GROQ_API_KEY

    selected_provider = (provider or "auto").lower().strip()

    if selected_provider in ["openrouter", "openrouter_free"]:
        converted_code = convert_with_openrouter(python_code, target_language, openrouter_key)
        if converted_code:
            provider_used = "OpenRouter AI (Free)"

    elif selected_provider == "groq":
        converted_code = convert_with_groq(python_code, target_language, groq_key)
        if converted_code:
            provider_used = "Groq Llama 3.3"

    elif selected_provider == "gemini":
        converted_code = await convert_with_gemini(python_code, target_language, gemini_key)
        if converted_code:
            provider_used = "Google Gemini AI"

    if not converted_code and selected_provider == "auto":
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            converted_code = await convert_with_gemini(python_code, target_language, gemini_key)
            if converted_code:
                provider_used = "Google Gemini AI"
        
        if not converted_code:
            converted_code = convert_with_openrouter(python_code, target_language, openrouter_key)
            if converted_code:
                provider_used = "OpenRouter Free AI"

        if not converted_code and groq_key:
            converted_code = convert_with_groq(python_code, target_language, groq_key)
            if converted_code:
                provider_used = "Groq Llama 3.3"

    if not converted_code:
        converted_code = convert_offline_fallback(python_code, target_language)
        provider_used = "Built-in PyMorph Morpher (Offline)"

    cleaned_code = clean_markdown_code_blocks(converted_code)
    elapsed_time = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "success": True,
        "converted_code": cleaned_code,
        "target_language": lang_info["name"],
        "language_info": lang_info,
        "provider": provider_used,
        "execution_time_ms": elapsed_time,
        "error": None
    }
