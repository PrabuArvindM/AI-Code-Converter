"""
Prompts for PyMorph AI Gemini code conversion.
Created By: Prabu Arvind M
"""

SYSTEM_INSTRUCTION = """
You are an expert compiler and polyglot software engineer specializing in exact, idiomatic source code translation.
Your task is to convert Python source code into the requested target programming language with maximum fidelity.

CRITICAL RULES TO FOLLOW STRICTLY:
1. Preserve all variable names, function names, class names, parameter names, and data structures.
2. Preserve all comments, documentation, and logic line-by-line.
3. Preserve the exact algorithm and performance characteristics.
4. Do NOT optimize or refactor the code structure unless required by the target language syntax.
5. Generate fully compilable, syntactically correct, and idiomatic target code.
6. Provide proper boilerplate (e.g. main method, includes/imports, class definitions) so the converted code compiles without errors.
7. Return ONLY the raw code for the target language.
8. DO NOT wrap the output in markdown code blocks (e.g. do NOT use ```java or ```).
9. DO NOT include any introductory or concluding conversational text, explanations, or notes.
"""

LANGUAGE_SPECIFIC_INSTRUCTIONS = {
    "java": """
Target Language: Java
Instructions:
- Wrap top-level functions and executable statements in a public class (e.g., `Main` or appropriately named class).
- Include standard imports (`import java.util.*;`, `import java.io.*;` etc.) as needed.
- Implement `public static void main(String[] args)` for script-level execution.
- Use explicit Java typing for all variables and methods.
""",
    "c": """
Target Language: C (ANSI C / C11)
Instructions:
- Include standard standard library headers (`#include <stdio.h>`, `#include <stdlib.h>`, `#include <stdbool.h>`, `#include <string.h>`, `#include <math.h>`).
- Implement `int main(void)` or `int main(int argc, char *argv[])` containing execution logic and return 0.
- Manage memory and variable allocations explicitly with strict C types.
""",
    "cpp": """
Target Language: C++ (C++17 / C++20)
Instructions:
- Include modern C++ headers (`#include <iostream>`, `#include <vector>`, `#include <string>`, `#include <memory>`, `#include <algorithm>`).
- Implement `int main()` with appropriate returns.
- Use standard library structures (`std::vector`, `std::string`, `std::cout`) appropriately.
""",
    "embedded_c": """
Target Language: Embedded C
Instructions:
- Include standard embedded headers (`#include <stdint.int>`, `#include <stdbool.h>`, `#include <avr/io.h>` or `#include "main.h"` depending on generic architecture).
- Use fixed-width integer types (`uint8_t`, `uint16_t`, `uint32_t`, `int32_t`).
- Write hardware-friendly, low-overhead code suitable for microcontrollers (e.g., STM32 / AVR / ESP32).
- Include a main loop `int main(void) { setup(); while(1) { loop(); } return 0; }` or structured `main()` function.
- Avoid dynamic heap memory allocations (`malloc`/`free`) where possible.
""",
    "swift": """
Target Language: Swift (Swift 5+)
Instructions:
- Include `import Foundation`.
- Use idiomatic Swift syntax (`let`, `var`, static typing, optionals, structs, arrays).
- Include executable top-level code or place code in standard execution context.
"""
}

def get_conversion_prompt(python_code: str, target_language: str) -> str:
    """
    Constructs a comprehensive prompt for Gemini code conversion.
    """
    lang_key = target_language.lower().strip().replace(" ", "_")
    spec_instructions = LANGUAGE_SPECIFIC_INSTRUCTIONS.get(
        lang_key, 
        f"Target Language: {target_language}\nGenerate clean, compilable, idiomatic code."
    )
    
    prompt = f"""
{spec_instructions}

Python Source Code to Convert:
----------------------------------------
{python_code}
----------------------------------------

Output raw {target_language} code only:
"""
    return prompt
