import re
import os


def parse_fixes(response_text):
    fixes = []

    text = re.sub(r'^\[.*?\]\s*\n', '', response_text).strip()

    blocks = re.split(r'(?=File:)', text, flags=re.IGNORECASE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        file_match = re.search(r'File:\s*(.+)', block, re.IGNORECASE)
        line_match = re.search(r'Line:\s*(\d+)', block, re.IGNORECASE)
        change_match = re.search(r'Change:\s*replace\s*`([^`]*)`\s*with\s*`([^`]*)`', block, re.IGNORECASE)

        if file_match and line_match and change_match:
            fixes.append({
                "file": file_match.group(1).strip(),
                "line": int(line_match.group(1).strip()),
                "old_code": change_match.group(1),
                "new_code": change_match.group(2),
            })

    return fixes


def apply_fixes(fixes, project_folder):
    if not fixes:
        return "No fixes found in AI response to apply."

    results = []

    for fix in fixes:
        file_path = fix["file"]

        if not os.path.isabs(file_path):
            file_path = os.path.join(project_folder, file_path)

        if not os.path.exists(file_path):
            results.append(f"✗ File not found: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            line_idx = fix["line"] - 1

            if line_idx < 0 or line_idx >= len(lines):
                results.append(f"✗ Line {fix['line']} out of range in {os.path.basename(file_path)}")
                continue

            original_line = lines[line_idx].rstrip('\n')
            old_code = fix["old_code"]
            new_code = fix["new_code"]

            if old_code not in original_line:
                found = False
                for offset in range(-3, 4):
                    idx = line_idx + offset
                    if 0 <= idx < len(lines) and old_code in lines[idx]:
                        line_idx = idx
                        original_line = lines[line_idx].rstrip('\n')
                        found = True
                        break

                if not found:
                    results.append(
                        f"✗ Could not find `{old_code}` near line {fix['line']} "
                        f"in {os.path.basename(file_path)}"
                    )
                    continue

            new_line = lines[line_idx].replace(old_code, new_code)
            lines[line_idx] = new_line

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            actual_line = line_idx + 1
            results.append(
                f"✓ {os.path.basename(file_path)} — Line {actual_line}\n"
                f"  - {original_line.strip()}\n"
                f"  + {new_line.strip()}"
            )

        except Exception as e:
            results.append(f"✗ Error applying fix to {os.path.basename(file_path)}: {str(e)}")

    return "\n\n".join(results)