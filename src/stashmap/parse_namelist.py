"""Parse namelist text into typed section objects."""
from pathlib import Path
import re
from typing import List, Union
from .parse_core import classify_record, BaseSection


def _split_blocks(lines: List[str]) -> List[List[str]]:
    starts = [i for i, L in enumerate(lines) if re.match(r"^\[!?\s*namelist:[^\]]+\]", L)]
    if not starts:
        return []
    ends = starts[1:] + [len(lines)]
    return [lines[s:e] for s, e in zip(starts, ends)]


def read_namelist(input_src: Union[str, Path], print_summary: bool = True) -> List[BaseSection]:
    """Read a namelist text or file into classified section objects.

    Parameters
    ----------
    input_src : str or pathlib.Path
        Path to a namelist file, or a string containing the namelist text.
    print_summary : bool, optional
        If True, print a brief summary of parsed section counts (default True).

    Returns
    -------
    list of BaseSection
        A list of section objects (instances of subclasses of ``BaseSection``).
    """
    if isinstance(input_src, (str, Path)):
        p = Path(input_src)
        if p.exists():
            text = p.read_text()
        else:
            text = str(input_src)
    else:
        text = str(input_src)

    lines = [ln.strip() for ln in text.splitlines()]
    blocks = _split_blocks(lines)
    records = []

    allowed_types = {'umstash_use', 'umstash_time', 'umstash_domain', 'umstash_streq', 'nlstcall_pp'}

    for block in blocks:
        header = block[0]
        sect_m = re.match(r"^\[!?\s*namelist:([^\(\]]+)", header)
        section_type = sect_m.group(1).strip() if sect_m else None
        if section_type not in allowed_types:
            continue
        incl = not header.startswith("[!namelist")
        m = re.search(r"\(([^)]+)\)", header)
        stash_id = m.group(1) if m else None
        rec = {"id": stash_id, "incl": incl, "section": section_type}
        last_key = None
        for line in block[1:]:
            if not line:
                continue
            if line.lstrip().startswith('='):
                cont = line.lstrip()[1:].strip().strip("'")
                if last_key and last_key in rec:
                    prev = '' if rec.get(last_key) is None else str(rec.get(last_key))
                    if prev.endswith(',') or cont.startswith(','):
                        new = prev + cont.lstrip(',')
                    elif prev == '':
                        new = cont
                    else:
                        new = prev + ',' + cont
                    rec[last_key] = new
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'")
                rec[k] = v
                last_key = k
        records.append(classify_record(rec))

    if print_summary:
        counts = {}
        for r in records:
            name = type(r).__name__
            active, total_c = counts.get(name, (0, 0))
            total_c += 1
            if getattr(r, 'incl', True):
                active += 1
            counts[name] = (active, total_c)
        total = len(records)
        summary = ", ".join(f"{k}: {v[0]}/{v[1]}" for k, v in sorted(counts.items()))
        print(f"Parsed {total} sections — {summary}")
    return records


"""Write namelist files from CSV rows or parsed sections."""
from pathlib import Path
import csv
import hashlib
from typing import List, Union
from .parse_core import BaseSection


def write_namelist(input_src: Union[str, Path, List[BaseSection]], output_txt: str):
    """Write a namelist file from CSV rows or parsed section list produced by read_namelist().

    Parameters
    ----------
    input_src : str or pathlib.Path or list of BaseSection
    output_txt : str
        Path to the output namelist text file to write.
    """
    def generate_suffix(isec, item, dom_name, tim_name):
        data = f"{isec}:{item}:{dom_name}:{tim_name}".encode()
        return hashlib.sha256(data).hexdigest()[:8]

    def _write_sections(sections: List[BaseSection], out_path: str):
        class_map = {
            'Variable': 'umstash_streq',
            'TimeProfile': 'umstash_time',
            'DomainProfile': 'umstash_domain',
            'UseProfile': 'umstash_use',
            'OutputStream': 'nlstcall_pp',
        }
        with open(out_path, 'w') as out:
            for section in sections:
                incl = getattr(section, 'incl', True)
                sid = None
                sect_name = None
                if isinstance(section.record, dict):
                    sid = section.record.get('id')
                    sect_name = section.record.get('section')
                if not sect_name:
                    sect_name = class_map.get(type(section).__name__, type(section).__name__.lower())
                if sid:
                    out.write(f"[{'!' if not incl else ''}namelist:{sect_name}({sid})]\n")
                else:
                    out.write(f"[{'!' if not incl else ''}namelist:{sect_name}]\n")
                def _wrap_val(key, value, sect_name):
                    # keep numeric scalars and booleans unquoted; keep lists unquoted
                    if value is None:
                        return f"{key}=''"
                    s = str(value).strip()
                    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                        s = s[1:-1]
                    low = s.lower()
                    if low in ('.true.', '.false.'):
                        return f"{key}={low}"
                    if low in ('true', 't'):
                        return f"{key}=.true."
                    if low in ('false', 'f'):
                        return f"{key}=.false."
                    if ',' in s:
                        # clean empty items and write single unquoted line
                        items = [it.strip() for it in s.split(',') if it and it.strip()]
                        return f"{key}=" + ','.join(items)
                    if s.replace('.', '', 1).lstrip('-').isdigit():
                        return f"{key}={s}"
                    return f"{key}='{s}'"
                for key, value in (section.record or {}).items():
                    if key in ('section', 'id', 'incl'):
                        continue
                    if key == 'variable_name' and sect_name == 'umstash_streq':
                        continue
                    out.write(_wrap_val(key, value, sect_name) + '\n')
                out.write('\n')

    if isinstance(input_src, (list, tuple)):
        _write_sections(list(input_src), output_txt)
        return None

    csv_path = Path(str(input_src))
    with open(csv_path, newline='') as f, open(output_txt, 'w') as out:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                isec = int(row.get('ISEC', 0))
                item = int(row.get('ITEM', 0))
            except Exception:
                isec = 0
                item = 0
            dom_name = row.get('DOM PROFILE', row.get('dom_name', '')).strip()
            use_name = row.get('USE', row.get('use_name', '')).strip()
            package = row.get('PACKAGE', row.get('package', '')).strip()
            tim_name = row.get('TIME PROFILE', row.get('tim_name', '')).strip()
            suffix = f"{isec:02d}{item:03d}_{generate_suffix(isec, item, dom_name, tim_name)}"
            out.write(f"[namelist:umstash_streq({suffix})]\n")
            if dom_name:
                out.write(f"dom_name='{dom_name}'\n")
            out.write(f"isec={isec}\n")
            out.write(f"item={item}\n")
            if package:
                out.write(f"package='{package}'\n")
            if tim_name:
                out.write(f"tim_name='{tim_name}'\n")
            if use_name:
                out.write(f"use_name='{use_name}'\n")
            out.write("\n")
    return None
