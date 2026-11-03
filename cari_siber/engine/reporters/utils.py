import re

def slugify(name: str) -> str:
    """Mengubah nama aplikasi menjadi slug nama_file_yang_aman."""
    val = name.replace("&", "dan")
    val = re.sub(r'[^\w\s-]', '', val).strip().lower()
    return re.sub(r'[-\s]+', '_', val)


def parse_markdown_section(md_content: str, section_keyword: str) -> str:
    """Mengambil baris-baris ulasan dalam satu section Markdown berdasarkan keyword."""
    if not md_content:
        return ""
    lines = md_content.split('\n')
    found = False
    section_lines = []
    for line in lines:
        stripped = line.strip()
        # Cocokkan hanya heading ## (H2) dan bukan ### (H3) atau yang lebih dalam
        is_h2 = stripped.startswith('##') and not stripped.startswith('###')
        if is_h2 and section_keyword.lower() in stripped.lower():
            found = True
            continue
        elif found:
            if is_h2:
                break
            section_lines.append(line)
    return '\n'.join(section_lines).strip()
