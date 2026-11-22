import os
import re
import json
import shutil
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT_DIR = Path(__file__).parent.resolve()
PROJECTS_DIR = ROOT_DIR / "output" / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def get_next_project_id() -> str:
    """
    Finds the highest existing pr-N folder number in output/projects and returns 'pr-{N+1}'.
    If no pr- folders exist, returns 'pr-1'.
    """
    max_id = 0
    if PROJECTS_DIR.exists():
        for d in PROJECTS_DIR.iterdir():
            if d.is_dir():
                m = re.match(r"^pr-(\d+)$", d.name.lower())
                if m:
                    num = int(m.group(1))
                    if num > max_id:
                        max_id = num
    return f"pr-{max_id + 1}"


def get_project_dir(project_id: str) -> Path:
    """Returns the Path to a given project folder in output/projects/."""
    safe_id = os.path.basename(project_id.strip())
    p_dir = PROJECTS_DIR / safe_id
    p_dir.mkdir(parents=True, exist_ok=True)
    return p_dir


def load_project_meta(project_id: str) -> Optional[Dict[str, Any]]:
    """Loads project_meta.json for a project."""
    p_dir = PROJECTS_DIR / os.path.basename(project_id.strip())
    meta_path = p_dir / "project_meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def is_project_blank(project_id: Optional[str]) -> bool:
    """Returns True if the project does not exist or contains no code/content files (empty or only project_meta.json)."""
    if not project_id:
        return True
    safe_id = os.path.basename(str(project_id).strip())
    p_dir = PROJECTS_DIR / safe_id
    if not p_dir.exists() or not p_dir.is_dir():
        return True
    
    # Check for any code or asset files
    for f in p_dir.rglob("*"):
        if f.is_file() and f.name != "project_meta.json":
            rel_str = str(f.relative_to(p_dir)).replace("\\", "/")
            if not rel_str.startswith(".backup"):
                return False
    return True


def create_new_project(
    project_id: Optional[str] = None,
    prompt: str = "",
    title: str = "",
    parent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new project folder inside output/projects/ with an incremental project ID (pr-1, pr-2, etc.).
    Initializes project_meta.json.
    """
    if not project_id:
        project_id = get_next_project_id()

    p_dir = get_project_dir(project_id)
    now_str = datetime.now().isoformat()

    if not title:
        if prompt:
            clean_title = re.sub(r'^(build|create|generate|design|make)\s+(a|an|the)?\s*', '', prompt, flags=re.IGNORECASE).strip()
            words = clean_title.split()[:4]
            title = " ".join(words).title() if words else f"Project {project_id.upper()}"
        else:
            title = f"Project {project_id.upper()}"

    meta = {
        "id": project_id,
        "title": title,
        "prompt": prompt,
        "parent_id": parent_id,
        "created_at": now_str,
        "updated_at": now_str,
        "files": [],
        "is_modified": bool(parent_id)
    }

    meta_path = p_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


def fork_project_for_modification(
    parent_id: str,
    modification_prompt: str = ""
) -> Tuple[str, Dict[str, Any]]:
    """
    Safely creates a new incremental project folder inside output/projects/ (e.g., pr-2 from pr-1)
    and copies all files and folders from parent_id into the new project folder.
    This guarantees the parent project code is NEVER overwritten.
    """
    new_id = get_next_project_id()
    new_dir = get_project_dir(new_id)
    parent_dir = PROJECTS_DIR / os.path.basename(parent_id.strip())

    # Recursively copy all existing files from parent to child
    if parent_dir.exists() and parent_dir.is_dir():
        for item in parent_dir.rglob("*"):
            if item.is_file() and item.name != "project_meta.json":
                rel = item.relative_to(parent_dir)
                dest = new_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    # Determine title
    parent_meta = load_project_meta(parent_id) or {}
    base_title = parent_meta.get("title", f"Project {parent_id.upper()}")
    new_title = f"{base_title} (Mod: {new_id})"

    now_str = datetime.now().isoformat()
    meta = {
        "id": new_id,
        "title": new_title,
        "prompt": modification_prompt or parent_meta.get("prompt", ""),
        "parent_id": parent_id,
        "created_at": now_str,
        "updated_at": now_str,
        "files": [str(f.relative_to(new_dir)).replace("\\", "/") for f in new_dir.rglob("*") if f.is_file() and f.name != "project_meta.json"],
        "is_modified": True
    }

    meta_path = new_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def find_balanced_tag(text: str, tag: str, start_pos: int) -> Optional[int]:
    """Finds the ending index of a balanced HTML tag, correctly handling arbitrary nested tags."""
    open_tag = re.compile(rf'<{tag}\b[^>]*>', re.IGNORECASE)
    close_tag = re.compile(rf'</{tag}>', re.IGNORECASE)
    pos = start_pos
    m_open = open_tag.match(text, pos)
    if not m_open:
        return None
    depth = 1
    pos = m_open.end()
    while depth > 0 and pos < len(text):
        next_open = open_tag.search(text, pos)
        next_close = close_tag.search(text, pos)
        if not next_close:
            return None
        if next_open and next_open.start() < next_close.start():
            depth += 1
            pos = next_open.end()
        else:
            depth -= 1
            pos = next_close.end()
    return pos


def apply_search_replace(existing_text: str, patch_text: str) -> Tuple[str, bool]:
    """Applies <<<<<<< SEARCH ... ======= ... >>>>>>> blocks to existing_text with CRLF and indentation tolerance."""
    if not patch_text or not existing_text:
        return existing_text, False

    clean_existing = existing_text.replace("\r\n", "\n")
    clean_patch = patch_text.replace("\r\n", "\n")

    pattern = re.compile(r"<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>>", re.DOTALL)
    matches = list(pattern.finditer(clean_patch))
    if not matches:
        return existing_text, False

    updated = clean_existing
    applied_any = False
    for m in matches:
        search_block = m.group(1)
        replace_block = m.group(2)

        # 1. Direct match (CRLF normalized)
        if search_block in updated:
            updated = updated.replace(search_block, replace_block, 1)
            applied_any = True
            continue

        # 2. Trailing whitespace normalized match
        norm_search = "\n".join(l.rstrip() for l in search_block.split("\n"))
        lines = updated.split("\n")
        search_lines = norm_search.split("\n")
        matched = False
        for i in range(len(lines) - len(search_lines) + 1):
            chunk = "\n".join(l.rstrip() for l in lines[i:i+len(search_lines)])
            if chunk == norm_search:
                lines[i:i+len(search_lines)] = replace_block.split("\n")
                updated = "\n".join(lines)
                applied_any = True
                matched = True
                break

        if matched:
            continue

        # 3. Indentation & stripped whitespace line-by-line match
        stripped_search = [l.strip() for l in search_block.split("\n") if l.strip()]
        if stripped_search:
            doc_lines = updated.split("\n")
            for i in range(len(doc_lines)):
                chunk = [l.strip() for l in doc_lines[i:] if l.strip()]
                if len(chunk) >= len(stripped_search) and chunk[:len(stripped_search)] == stripped_search:
                    matched_count = 0
                    end_idx = i
                    for j in range(i, len(doc_lines)):
                        if doc_lines[j].strip():
                            matched_count += 1
                        if matched_count == len(stripped_search):
                            end_idx = j + 1
                            break
                    doc_lines[i:end_idx] = replace_block.split("\n")
                    updated = "\n".join(doc_lines)
                    applied_any = True
                    break

    return updated, applied_any


def extract_component_context(file_content: str, target_selector_or_id: str, file_type: str = "html") -> str:
    """
    Extracts the targeted element / rule / function and its local context
    from the baseline file so workers are not blind.
    """
    if not file_content:
        return ""
    if not target_selector_or_id:
        return file_content[:3500]

    raw_target = target_selector_or_id.strip()
    target_clean = raw_target.lstrip("#").lstrip(".")

    if file_type == "html":
        # 1. Search by id
        id_pattern = re.compile(rf'<([a-zA-Z0-9]+)\b[^>]*id=["\']{re.escape(target_clean)}["\']', re.IGNORECASE)
        m = id_pattern.search(file_content)
        if m:
            tag = m.group(1)
            end_pos = find_balanced_tag(file_content, tag, m.start())
            if end_pos:
                start_ctx = max(0, file_content.rfind("\n", 0, max(0, m.start() - 300)))
                end_ctx = min(len(file_content), file_content.find("\n", min(len(file_content), end_pos + 300)))
                if end_ctx == -1:
                    end_ctx = len(file_content)
                return file_content[start_ctx:end_ctx].strip()

        # 2. Search by class
        class_pattern = re.compile(rf'<([a-zA-Z0-9]+)\b[^>]*class=["\'][^"\']*\b{re.escape(target_clean)}\b[^"\']*["\']', re.IGNORECASE)
        m = class_pattern.search(file_content)
        if m:
            tag = m.group(1)
            end_pos = find_balanced_tag(file_content, tag, m.start())
            if end_pos:
                start_ctx = max(0, file_content.rfind("\n", 0, max(0, m.start() - 300)))
                end_ctx = min(len(file_content), file_content.find("\n", min(len(file_content), end_pos + 300)))
                if end_ctx == -1:
                    end_ctx = len(file_content)
                return file_content[start_ctx:end_ctx].strip()

        # 3. Search by tag name (<nav>, <header>, <section>, etc.)
        tag_pattern = re.compile(rf'<({re.escape(target_clean)})\b', re.IGNORECASE)
        m = tag_pattern.search(file_content)
        if m:
            end_pos = find_balanced_tag(file_content, target_clean, m.start())
            if end_pos:
                return file_content[m.start():end_pos].strip()

    elif file_type == "css":
        # Search for selector rule block, e.g. .target or #target or target
        esc_target = re.escape(raw_target)
        pattern = re.compile(rf'([^{{}}]*?{esc_target}\s*\{{[^}}]*\}})', re.DOTALL)
        m = pattern.search(file_content)
        if m:
            return m.group(1).strip()

    elif file_type == "js":
        # Search for function name
        func_pattern = re.compile(rf'(function\s+{re.escape(target_clean)}\s*\([^\)]*\)\s*\{{[\s\S]*?\n\}})', re.MULTILINE)
        m = func_pattern.search(file_content)
        if m:
            return m.group(1).strip()
        # Search for variable / listener
        var_pattern = re.compile(rf'((?:const|let|var)\s+{re.escape(target_clean)}\s*=[\s\S]*?;)', re.MULTILINE)
        m = var_pattern.search(file_content)
        if m:
            return m.group(1).strip()

    # Fallback to search query substring with surrounding context window
    idx = file_content.lower().find(target_clean.lower())
    if idx != -1:
        start_pos = max(0, idx - 400)
        end_pos = min(len(file_content), idx + 1200)
        return file_content[start_pos:end_pos].strip()

    return file_content[:3500]


def replace_or_append_html(existing_html: str, snippet: str) -> str:
    """
    Surgically replaces or appends an HTML component without rebuilding from scratch.
    - If snippet contains <<<<<<< SEARCH ... ======= ... >>>>>>> blocks, applies exact patch.
    - If snippet matches an existing element ID, replaces only that element.
    - If snippet matches an existing element class, replaces that element in-place.
    - If snippet matches structural tags (<header>, <nav>, <footer>), updates that element.
    - Protects existing layout and unmentioned sections from being wiped.
    """
    snippet_clean = snippet.strip()
    if not snippet_clean:
        return existing_html
    if not existing_html:
        return snippet_clean

    # 1. Check for search/replace blocks first
    patched_html, applied = apply_search_replace(existing_html, snippet_clean)
    if applied:
        return patched_html

    # 2. Check if snippet has an ID
    id_match = re.search(r'<([a-zA-Z0-9]+)[^>]*id=["\']([^"\']+)["\']', snippet_clean, re.IGNORECASE)
    if id_match:
        tag = id_match.group(1).lower()
        elem_id = id_match.group(2)
        pattern = re.compile(rf'<({tag})\b[^>]*id=["\']{re.escape(elem_id)}["\']', re.IGNORECASE)
        m = pattern.search(existing_html)
        if m:
            matched_tag = m.group(1)
            end_pos = find_balanced_tag(existing_html, matched_tag, m.start())
            if end_pos:
                return existing_html[:m.start()] + snippet_clean + existing_html[end_pos:]

    # 3. Check if snippet has a distinctive class matching an existing element
    class_match = re.search(r'<([a-zA-Z0-9]+)[^>]*class=["\']([^"\']+)["\']', snippet_clean, re.IGNORECASE)
    if class_match:
        tag = class_match.group(1).lower()
        classes = [c.strip() for c in class_match.group(2).split() if c.strip() and not c.startswith("glass-") and not c in ["btn", "active", "show", "modal"]]
        for cls in classes:
            pattern = re.compile(rf'<({tag})\b[^>]*class=["\'][^"\']*\b{re.escape(cls)}\b[^"\']*["\']', re.IGNORECASE)
            m = pattern.search(existing_html)
            if m:
                matched_tag = m.group(1)
                end_pos = find_balanced_tag(existing_html, matched_tag, m.start())
                if end_pos:
                    return existing_html[:m.start()] + snippet_clean + existing_html[end_pos:]

    # 4. Check for structural tags without ID (<header>, <nav>, <footer>)
    for stag in ["header", "nav", "footer"]:
        if snippet_clean.lower().startswith(f"<{stag}") and snippet_clean.lower().endswith(f"</{stag}>"):
            m = re.search(rf'<{stag}\b', existing_html, re.IGNORECASE)
            if m:
                end_pos = find_balanced_tag(existing_html, stag, m.start())
                if end_pos:
                    return existing_html[:m.start()] + snippet_clean + existing_html[end_pos:]

    # 5. Full document fallback check
    if "<!doctype" in snippet_clean.lower() or "<html" in snippet_clean.lower():
        existing_sections = re.findall(r'<section\b', existing_html, re.IGNORECASE)
        new_sections = re.findall(r'<section\b', snippet_clean, re.IGNORECASE)
        if len(existing_sections) >= 2 and len(new_sections) <= 1:
            sec_match = re.search(r'(<section[\s\S]*?</section>)', snippet_clean, re.IGNORECASE)
            if sec_match:
                extracted_section = sec_match.group(1)
                return replace_or_append_html(existing_html, extracted_section)
        return snippet_clean

    # 6. Append new component only if it is a recognized structural addition (<section>, modal dialog)
    is_structural = (
        snippet_clean.lower().startswith("<section") or
        snippet_clean.lower().startswith("<aside") or
        snippet_clean.lower().startswith("<dialog") or
        'id="modal' in snippet_clean.lower() or
        'class="modal' in snippet_clean.lower()
    )
    if is_structural:
        footer_match = re.search(r'(<footer\b)', existing_html, re.IGNORECASE)
        if footer_match:
            idx = footer_match.start()
            return existing_html[:idx] + f"{snippet_clean}\n\n  " + existing_html[idx:]
        if "</main>" in existing_html:
            return existing_html.replace("</main>", f"  {snippet_clean}\n</main>", 1)
        if "</body>" in existing_html:
            return existing_html.replace("</body>", f"  {snippet_clean}\n</body>", 1)

    # Unmatched non-structural fragment: retain existing HTML to protect layout integrity
    return existing_html


def merge_css(existing_css: str, new_css: str) -> str:
    """
    Surgically merges CSS rules into existing_css without wiping or duplicating existing styles.
    - If new_css contains search/replace blocks, applies them directly.
    - If new_css contains rule blocks (selector { ... }):
      - Replaces matching selectors in-place in existing_css.
      - Gathers truly new selectors and appends only those new rules cleanly.
    - Never cascades the whole stylesheet or duplicates rules.
    """
    new_css_clean = new_css.strip()
    if not existing_css:
        return new_css_clean
    if not new_css_clean or new_css_clean in existing_css:
        return existing_css

    # 1. Search & Replace check
    patched, applied = apply_search_replace(existing_css, new_css_clean)
    if applied:
        return patched

    # 2. Extract CSS rule blocks from new_css: selector { declarations }
    # Avoid media queries in simple rule regex by extracting top-level or inner rules
    rule_regex = re.compile(r'([^{}]+?)\s*\{\s*([^{}]+?)\s*\}', re.DOTALL)
    new_rules = list(rule_regex.finditer(new_css_clean))

    if not new_rules:
        # If it's a raw snippet without braces, append cleanly
        now_tag = datetime.now().strftime("%H:%M:%S")
        return f"{existing_css.rstrip()}\n\n/* --- Surgical Modifier Update ({now_tag}) --- */\n{new_css_clean}\n"

    updated_css = existing_css
    new_rules_to_append = []

    for nr in new_rules:
        raw_selector = nr.group(1).strip()
        declarations = nr.group(2).strip()
        full_rule = f"{raw_selector} {{\n  {declarations}\n}}"

        # Try to find existing rule with this exact selector
        # Look for: raw_selector { ... }
        esc_sel = re.escape(raw_selector)
        exist_pattern = re.compile(rf'(^|[;}}\n]\s*)({esc_sel})\s*\{{[^{{}}]*?\}}', re.MULTILINE)
        m = exist_pattern.search(updated_css)

        if m:
            # Replace existing rule in-place
            prefix = m.group(1)
            start_idx = m.start() + len(prefix)
            end_idx = m.end()
            updated_css = updated_css[:start_idx] + full_rule + updated_css[end_idx:]
        else:
            new_rules_to_append.append(full_rule)

    if new_rules_to_append:
        now_tag = datetime.now().strftime("%H:%M:%S")
        added_block = "\n\n".join(new_rules_to_append)
        updated_css = f"{updated_css.rstrip()}\n\n/* --- Surgical Modifier Update ({now_tag}) --- */\n{added_block}\n"

    return updated_css


def merge_js(existing_js: str, new_js: str) -> str:
    """
    Surgically merges JS logic into existing_js without wiping existing listeners or duplicating scripts.
    - If new_js contains search/replace blocks, applies them directly.
    - If new_js defines functions, updates matched functions in-place using balanced braces.
    - If new listeners are added, ensures they are appended cleanly without duplicate calls.
    """
    new_js_clean = new_js.strip()
    if not existing_js:
        return new_js_clean
    if not new_js_clean or new_js_clean in existing_js:
        return existing_js

    # 1. Search & Replace check
    patched, applied = apply_search_replace(existing_js, new_js_clean)
    if applied:
        return patched

    # 2. Check for function replacements
    func_matches = list(re.finditer(r'function\s+([a-zA-Z0-9_$]+)\s*\([^\)]*\)\s*\{', new_js_clean))
    updated_js = existing_js
    replaced_any = False
    replaced_functions = set()

    for fm in func_matches:
        fn_name = fm.group(1)
        exist_pattern = re.compile(r'function\s+' + re.escape(fn_name) + r'\s*\([^\)]*\)\s*\{', re.MULTILINE)
        em = exist_pattern.search(updated_js)
        if em:
            open_idx = updated_js.find("{", em.start())
            if open_idx != -1:
                depth = 1
                pos = open_idx + 1
                while depth > 0 and pos < len(updated_js):
                    if updated_js[pos] == "{":
                        depth += 1
                    elif updated_js[pos] == "}":
                        depth -= 1
                    pos += 1
                if depth == 0:
                    # Find function snippet in new_js
                    new_open = new_js_clean.find("{", fm.start())
                    ndepth = 1
                    npos = new_open + 1
                    while ndepth > 0 and npos < len(new_js_clean):
                        if new_js_clean[npos] == "{":
                            ndepth += 1
                        elif new_js_clean[npos] == "}":
                            ndepth -= 1
                        npos += 1
                    if ndepth == 0:
                        new_fn_code = new_js_clean[fm.start():npos]
                        updated_js = updated_js[:em.start()] + new_fn_code + updated_js[pos:]
                        replaced_any = True
                        replaced_functions.add(fn_name)

    # 3. If there are new non-function scripts or functions that weren't in existing_js:
    # Filter out functions that were already replaced in-place
    clean_additions = new_js_clean
    for fn in replaced_functions:
        clean_additions = re.sub(rf'function\s+{re.escape(fn)}\s*\([^\)]*\)\s*\{{[\s\S]*?\n\}}', '', clean_additions).strip()

    if clean_additions and clean_additions not in updated_js:
        now_tag = datetime.now().strftime("%H:%M:%S")
        return f"{updated_js.rstrip()}\n\n// --- Surgical Modifier Update ({now_tag}) ---\n{clean_additions}\n"

    return updated_js


def get_backup_dir(project_id: str) -> Path:
    """Returns the Path to the single .backup folder inside the project."""
    p_dir = get_project_dir(project_id)
    return p_dir / ".backup"


def has_baseline_backup(project_id: str) -> bool:
    """Checks if a valid accepted baseline exists in .backup/."""
    b_dir = get_backup_dir(project_id)
    if not b_dir.exists() or not b_dir.is_dir():
        return False
    return any(f.is_file() for f in b_dir.rglob("*"))


def get_baseline_files(project_id: str) -> Dict[str, Any]:
    """
    Returns the pristine baseline files stored in .backup/.
    If no backup exists yet, falls back to active project files.
    """
    b_dir = get_backup_dir(project_id)
    if has_baseline_backup(project_id):
        files = {}
        for item in sorted(b_dir.rglob("*")):
            if item.is_file() and item.name != "project_meta.json":
                rel_name = str(item.relative_to(b_dir)).replace("\\", "/")
                ftype = get_file_type(item.name)
                try:
                    files[rel_name] = {
                        "content": item.read_text(encoding="utf-8"),
                        "size": item.stat().st_size,
                        "type": ftype,
                        "is_binary": False
                    }
                except Exception:
                    files[rel_name] = {
                        "content": None,
                        "size": item.stat().st_size,
                        "type": ftype,
                        "is_binary": True
                    }
        return files
    return get_project_files(project_id)


def save_baseline_version(project_id: str) -> bool:
    """
    Promotes the current working files to the single .backup/ baseline directory.
    Clears any prior contents in .backup/ so strictly ONE past accepted version is kept.
    """
    p_dir = get_project_dir(project_id)
    b_dir = get_backup_dir(project_id)

    # Clean existing backup
    if b_dir.exists():
        shutil.rmtree(b_dir, ignore_errors=True)
    b_dir.mkdir(parents=True, exist_ok=True)

    # Copy current project files (excluding backups and project_meta.json)
    for item in p_dir.iterdir():
        if item.name in [".backup", ".backups", "project_meta.json"]:
            continue
        if item.is_file():
            shutil.copy2(item, b_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, b_dir / item.name, dirs_exist_ok=True)

    # Clean any legacy timestamped .backups folders
    legacy_backups = p_dir / ".backups"
    if legacy_backups.exists():
        shutil.rmtree(legacy_backups, ignore_errors=True)

    return True


def promote_staged_to_baseline(project_id: str) -> Dict[str, Any]:
    """
    User clicked 'Like': Accepts current staged version as the official baseline.
    Overwrites .backup/ with current project root files.
    """
    p_dir = get_project_dir(project_id)
    save_baseline_version(project_id)

    meta = load_project_meta(project_id) or {}
    meta["review_status"] = "accepted"
    meta["last_accepted_at"] = datetime.now().isoformat()
    meta["updated_at"] = datetime.now().isoformat()

    meta_path = p_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"status": "ok", "project_id": project_id, "review_status": "accepted"}


def revert_staged_from_baseline(project_id: str) -> Dict[str, Any]:
    """
    User clicked 'Dislike': Reverts working root files back to the accepted .backup/ baseline.
    Next modifications will branch directly from this baseline.
    """
    p_dir = get_project_dir(project_id)
    b_dir = get_backup_dir(project_id)

    if not has_baseline_backup(project_id):
        return {"status": "error", "message": "No baseline backup found to revert to."}

    # Remove working files from p_dir (preserve .backup and project_meta.json)
    for item in p_dir.iterdir():
        if item.name in [".backup", ".backups", "project_meta.json"]:
            continue
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

    # Restore from .backup/
    for item in b_dir.iterdir():
        if item.is_file():
            shutil.copy2(item, p_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, p_dir / item.name, dirs_exist_ok=True)

    meta = load_project_meta(project_id) or {}
    meta["review_status"] = "rejected"
    meta["last_rejected_at"] = datetime.now().isoformat()
    meta["updated_at"] = datetime.now().isoformat()

    all_files = [str(f.relative_to(p_dir)).replace("\\", "/") for f in p_dir.rglob("*")
                 if f.is_file() and f.name != "project_meta.json" and ".backup" not in str(f)]
    meta["files"] = all_files

    meta_path = p_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"status": "ok", "project_id": project_id, "review_status": "rejected", "files": all_files}


def apply_surgical_modification(
    project_id: str,
    parsed_files: Dict[str, Any],
    modification_prompt: str = ""
) -> List[Dict[str, Any]]:
    """
    Surgically updates a project in-place on top of the accepted .backup/ baseline.
    Current root files show how the new code looks (staged preview).
    - If .backup/ does not exist, saves current files as baseline first.
    - Applies modifications on top of .backup/ baseline files.
    - Saves staged results to project root for user review (with Like/Dislike options).
    """
    p_dir = get_project_dir(project_id)
    b_dir = get_backup_dir(project_id)

    # 1. Ensure baseline exists before applying new upgrades
    if not has_baseline_backup(project_id):
        save_baseline_version(project_id)

    # 2. Re-align root files to baseline for any files not targeted by this modification
    for b_item in b_dir.rglob("*"):
        if b_item.is_file() and b_item.name != "project_meta.json":
            rel = b_item.relative_to(b_dir)
            target = p_dir / rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(b_item, target)

    saved = []

    # 3. Process each modified file on top of baseline
    for name, content in parsed_files.items():
        clean_name = name.replace("\\", "/").strip().lstrip("/")
        parts = [p for p in clean_name.split("/") if p and p != ".."]
        if not parts:
            continue
        rel_path = "/".join(parts)
        file_path = p_dir / rel_path
        baseline_file = b_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            is_changed = True
            if baseline_file.exists():
                try:
                    if baseline_file.read_bytes() == content:
                        is_changed = False
                except Exception:
                    pass
            file_path.write_bytes(content)
            if is_changed:
                saved.append({
                    "name": rel_path,
                    "path": str(file_path),
                    "size": len(content),
                    "type": get_file_type(file_path.name)
                })
            continue

        text_str = str(content).strip()
        # Read starting code from baseline backup (or existing root file if brand new file)
        if baseline_file.exists():
            base_text = baseline_file.read_text(encoding="utf-8")
        elif file_path.exists():
            base_text = file_path.read_text(encoding="utf-8")
        else:
            base_text = ""

        # Surgical Smart Merge on top of baseline
        if rel_path.endswith(".html"):
            if "<!doctype" in text_str.lower() or "<html" in text_str.lower():
                final_content = text_str
            else:
                final_content = replace_or_append_html(base_text, text_str)
        elif rel_path.endswith(".css"):
            if len(text_str) >= len(base_text) * 0.5 or not base_text:
                final_content = text_str
            else:
                final_content = merge_css(base_text, text_str)
        elif rel_path.endswith(".js"):
            if len(text_str) >= len(base_text) * 0.5 or not base_text:
                final_content = text_str
            else:
                final_content = merge_js(base_text, text_str)
        else:
            patched, applied = apply_search_replace(base_text, text_str)
            final_content = patched if applied else text_str

        file_path.write_text(final_content, encoding="utf-8")
        is_changed = (not baseline_file.exists()) or (final_content.strip() != base_text.strip())
        if is_changed:
            saved.append({
                "name": rel_path,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "type": get_file_type(file_path.name)
            })

    # If no files had net diffs, list primary target files so user sees confirmation
    if not saved and parsed_files:
        for name in list(parsed_files.keys()):
            clean_check = name.replace("\\", "/").strip().lstrip("/")
            if clean_check in ["index.html", "styles.css", "app.js"]:
                fp = p_dir / clean_check
                if fp.exists():
                    saved.append({
                        "name": clean_check,
                        "path": str(fp),
                        "size": fp.stat().st_size,
                        "type": get_file_type(fp.name)
                    })

    # Ensure connections in staged files
    ensure_project_file_connections(p_dir)

    # Refresh metadata in-place
    meta = load_project_meta(project_id) or {
        "id": project_id,
        "title": f"Project {project_id.upper()}",
        "prompt": modification_prompt,
        "parent_id": None,
        "created_at": datetime.now().isoformat(),
        "is_modified": False
    }

    all_files = [str(f.relative_to(p_dir)).replace("\\", "/") for f in p_dir.rglob("*")
                 if f.is_file() and f.name != "project_meta.json" and ".backup" not in str(f)]
    meta["files"] = all_files
    meta["updated_at"] = datetime.now().isoformat()
    meta["is_modified"] = True
    meta["review_status"] = "staged"
    if modification_prompt:
        meta["last_modification"] = modification_prompt

    meta_path = p_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return saved


def ensure_project_file_connections(p_dir: Path):
    """
    Ensures index.html links to styles.css and app.js if they exist in the project directory.
    """
    html_file = p_dir / "index.html"
    if not html_file.exists():
        return

    try:
        html_code = html_file.read_text(encoding="utf-8")
        modified = False

        # Link styles.css if present
        css_file = p_dir / "styles.css"
        if css_file.exists() and 'styles.css' not in html_code:
            link_tag = '<link rel="stylesheet" href="styles.css">'
            if "</head>" in html_code:
                html_code = html_code.replace("</head>", f"  {link_tag}\n</head>")
                modified = True
            elif "<head>" in html_code:
                html_code = html_code.replace("<head>", f"<head>\n  {link_tag}")
                modified = True

        # Link app.js if present
        js_file = p_dir / "app.js"
        if js_file.exists() and 'app.js' not in html_code:
            script_tag = '<script src="app.js" defer></script>'
            if "</body>" in html_code:
                html_code = html_code.replace("</body>", f"  {script_tag}\n</body>")
                modified = True
            elif "</head>" in html_code:
                html_code = html_code.replace("</head>", f"  {script_tag}\n</head>")
                modified = True

        if modified:
            html_file.write_text(html_code, encoding="utf-8")
    except Exception:
        pass


def save_files_to_project(
    project_id: str,
    files_dict: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Saves a dictionary of {filename: content (str or bytes)} to the project folder.
    Updates project_meta.json with file list and modification timestamp.
    """
    p_dir = get_project_dir(project_id)
    saved = []

    for name, content in files_dict.items():
        # Sanitize relative path (allow subfolders like css/styles.css while blocking traversal)
        clean_name = name.replace("\\", "/").strip().lstrip("/")
        parts = [p for p in clean_name.split("/") if p and p != ".."]
        if not parts:
            continue
        rel_path = "/".join(parts)
        
        file_path = p_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            file_path.write_bytes(content)
            saved.append({
                "name": rel_path,
                "path": str(file_path),
                "size": len(content),
                "type": get_file_type(file_path.name)
            })
        else:
            text_str = str(content)
            file_path.write_text(text_str, encoding="utf-8")
            saved.append({
                "name": rel_path,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "type": get_file_type(file_path.name)
            })

    # Ensure connections between index.html and styles.css/app.js
    ensure_project_file_connections(p_dir)

    # Refresh project metadata
    meta = load_project_meta(project_id) or {
        "id": project_id,
        "title": f"Project {project_id.upper()}",
        "prompt": "",
        "parent_id": None,
        "created_at": datetime.now().isoformat(),
        "is_modified": False
    }

    all_files = [str(f.relative_to(p_dir)).replace("\\", "/") for f in p_dir.rglob("*")
                 if f.is_file() and f.name != "project_meta.json" and ".backup" not in str(f)]
    meta["files"] = all_files
    meta["updated_at"] = datetime.now().isoformat()

    # If project has no baseline yet, initialize current files as baseline
    if not has_baseline_backup(project_id):
        save_baseline_version(project_id)
        meta["review_status"] = "accepted"
    else:
        meta["review_status"] = "staged"

    meta_path = p_dir / "project_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return saved


def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in [".html", ".htm"]:
        return "html"
    elif ext == ".css":
        return "css"
    elif ext in [".js", ".jsx", ".ts", ".tsx", ".mjs"]:
        return "javascript"
    elif ext == ".json":
        return "json"
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        return "image"
    elif ext == ".svg":
        return "svg"
    elif ext == ".py":
        return "python"
    elif ext in [".md", ".markdown"]:
        return "markdown"
    return "other"


def get_project_files(project_id: str) -> Dict[str, Any]:
    """
    Returns a dictionary of all text files and metadata for binary files in the project.
    Recursively scans any subfolders (e.g. css/, js/), strictly ignoring .backup/ folders.
    """
    p_dir = PROJECTS_DIR / os.path.basename(project_id.strip())
    files = {}
    if not p_dir.exists():
        return files

    for item in sorted(p_dir.rglob("*")):
        if item.is_file() and item.name != "project_meta.json":
            rel_name = str(item.relative_to(p_dir)).replace("\\", "/")
            if ".backup" in rel_name:
                continue
            ftype = get_file_type(item.name)
            if ftype in ["html", "css", "javascript", "json", "python", "svg", "markdown", "other"]:
                try:
                    files[rel_name] = {
                        "content": item.read_text(encoding="utf-8"),
                        "size": item.stat().st_size,
                        "type": ftype,
                        "is_binary": False
                    }
                except Exception:
                    files[rel_name] = {
                        "content": None,
                        "size": item.stat().st_size,
                        "type": ftype,
                        "is_binary": True
                    }
            else:
                files[rel_name] = {
                    "content": None,
                    "size": item.stat().st_size,
                    "type": ftype,
                    "is_binary": True
                }

    return files


def list_all_projects() -> List[Dict[str, Any]]:
    """
    Lists all pr-* projects in output/projects/ with their metadata, sorted by project number descending (newest first).
    """
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for d in PROJECTS_DIR.iterdir():
        if d.is_dir():
            m = re.match(r"^pr-(\d+)$", d.name.lower())
            if m:
                num = int(m.group(1))
                meta = load_project_meta(d.name)
                files_list = [str(f.relative_to(d)).replace("\\", "/") for f in d.rglob("*")
                              if f.is_file() and f.name != "project_meta.json" and ".backup" not in str(f)]
                if not meta:
                    meta = {
                        "id": d.name,
                        "title": f"Project {d.name.upper()}",
                        "prompt": "",
                        "parent_id": None,
                        "created_at": datetime.fromtimestamp(d.stat().st_ctime).isoformat(),
                        "updated_at": datetime.fromtimestamp(d.stat().st_mtime).isoformat(),
                        "files": files_list,
                        "is_modified": False,
                        "review_status": "accepted"
                    }
                meta["num"] = num
                meta["files"] = files_list
                meta["file_count"] = len(files_list)
                projects.append(meta)

    projects.sort(key=lambda x: x.get("num", 0), reverse=True)
    return projects



def parse_multi_file_response(text: str) -> Dict[str, Any]:
    """
    Extracts all code files, SVGs, and base64 images from the model's text response.
    Supports:
      1. Code blocks with language annotation: ```lang filename="path" or ```lang:path
      2. Code blocks with comment indicators on line 1:
         <!-- filename: index.html --> or // filename: app.js
      3. Markdown headings before code block:
         ### index.html\n```html ... ```
      4. Fallback standard single code blocks (HTML, CSS, JS, JSON, Python)
      5. Base64 data URI images and standalone SVGs
    """
    files: Dict[str, Any] = {}

    # 1. Base64 Data URI Images
    b64_matches = re.findall(r"data:image/([a-zA-Z0-9_\-+]+);base64,([A-Za-z0-9+/=\s]+)", text)
    img_counter = 1
    for img_format, b64_str in b64_matches:
        try:
            raw_bytes = base64.b64decode(b64_str.strip())
            ext = f".{img_format.lower()}"
            if ext == ".jpeg":
                ext = ".jpg"
            img_name = f"image_{img_counter}{ext}"
            files[img_name] = raw_bytes
            img_counter += 1
        except Exception:
            pass

    # 2. Standalone SVG
    svg_matches = re.findall(r"```(?:svg|xml)?\s*\n\s*(<svg[\s\S]*?</svg>)\s*```", text, re.IGNORECASE)
    if not svg_matches and not ("<!DOCTYPE html>" in text or "<html" in text):
        svg_matches = re.findall(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)

    svg_counter = 1
    for svg_content in svg_matches:
        svg_name = f"icon_{svg_counter}.svg"
        files[svg_name] = svg_content.strip()
        svg_counter += 1

    # 3. Explicit filename patterns in code fences:
    # Pattern A: ```lang filename="app.js" or ```lang file="app.js" or ```lang:app.js
    fence_pattern = re.compile(
        r"```(?P<lang>[a-zA-Z0-9_\-+]+)?(?:\s+(?:filename|file|path)=[\"'](?P<fn1>[^\"']+)[\"']|:(?P<fn2>[^\s\n]+))?\s*\n(?P<code>[\s\S]*?)(?:```|$)",
        re.IGNORECASE
    )

    for m in fence_pattern.finditer(text):
        lang = (m.group("lang") or "").lower()
        fn = m.group("fn1") or m.group("fn2")
        code = m.group("code").strip()
        if not code:
            continue

        # If no filename in fence, check first line comment
        if not fn:
            first_line = code.split("\n", 1)[0].strip()
            comment_match = re.match(
                r"^(?:<!--|//|#|/\*)\s*(?:filename|file|path)?:\s*([a-zA-Z0-9_\-\.\/\\]+)\s*(?:-->|\*/)?$",
                first_line,
                re.IGNORECASE
            )
            if comment_match:
                fn = comment_match.group(1).strip()
                # Remove the comment line from the code
                parts = code.split("\n", 1)
                code = parts[1].strip() if len(parts) > 1 else ""

        # Check if preceding text has a heading like: ### `index.html` or ### app.js
        if not fn:
            start_pos = m.start()
            preceding = text[max(0, start_pos - 150):start_pos]
            heading_match = re.search(r"#{2,4}\s*`?([a-zA-Z0-9_\-\.]+\.(?:html|css|js|json|py|svg|md|ts|jsx|tsx))`?", preceding)
            if heading_match:
                fn = heading_match.group(1).strip()

        # Fallback based on content/lang if still not identified
        if not fn:
            if lang in ["replace", "diff"]:
                if "<html" in code.lower() or "<section" in code.lower() or "<div" in code.lower() or "<button" in code.lower():
                    fn = "index.html"
                elif "{" in code and "}" in code and (":" in code or ";" in code):
                    fn = "styles.css"
                else:
                    fn = "app.js"
            elif lang in ["html", "htm"] or "<!doctype html" in code.lower() or "<html" in code.lower() or "<section" in code.lower() or "<div" in code.lower() or "<header" in code.lower() or "<footer" in code.lower() or "<nav" in code.lower():
                fn = "index.html"
            elif lang == "css" or ("{" in code and "}" in code and (":" in code or ";" in code) and "<html" not in code.lower()):
                fn = "styles.css"
            elif lang in ["js", "javascript"]:
                fn = "app.js"
            elif lang == "json":
                fn = "data.json"
            elif lang == "python":
                fn = "main.py"

        if fn and code:
            fn = os.path.basename(fn.strip())
            files[fn] = code

    # 4. Fallback: If no HTML or CSS were extracted by fences, run raw search
    if "index.html" not in files:
        html_match = re.search(r"```(?:html|htm)?\s*\n(.*?<!DOCTYPE html>.*?</html>|.*?<html.*?</html>)\s*(?:```|$)", text, re.DOTALL | re.IGNORECASE)
        if not html_match:
            raw_match = re.search(r"(<!DOCTYPE html>.*?</html>|<html.*?</html>)", text, re.DOTALL | re.IGNORECASE)
            if raw_match:
                files["index.html"] = raw_match.group(1).strip()
        else:
            files["index.html"] = html_match.group(1).strip()

    if "styles.css" not in files:
        css_match = re.search(r"```css\s*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
        if css_match:
            files["styles.css"] = css_match.group(1).strip()
        elif "index.html" in files:
            # Extract from <style> in HTML
            style_matches = re.findall(r"<style[^>]*>(.*?)</style>", files["index.html"], re.DOTALL | re.IGNORECASE)
            if style_matches:
                files["styles.css"] = "\n\n".join(s.strip() for s in style_matches if s.strip())

    return files
