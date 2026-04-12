import os
 
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".cpp", ".h", ".hpp", ".c",
    ".cs", ".java", ".go", ".rs",
    ".html", ".css", ".json", ".yaml", ".yml",
    ".lua", ".rb", ".php", ".swift", ".kt"
}
 
def read_specific_files(files):
    """Read files and return their contents with line numbers."""
    code = ""
 
    for path in files:
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue
 
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            code += f"\n\n{'='*60}\n"
            code += f"FILE: {path}\n"
            code += f"{'='*60}\n"

            for i, line in enumerate(lines, start=1):
                code += f"{i:4d} | {line}"
 
            if not lines[-1].endswith("\n"):
                code += "\n"
 
        except Exception as e:
            code += f"\n# Could not read {path}: {e}\n"
 
    return code
 