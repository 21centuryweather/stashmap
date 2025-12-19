"""Refactored parsing utilities for UM STASH namelist sections.

Provides:
- `parse_namelist(path_or_text)` -> list of classified section objects
- `generate_namelist_from_csv(input_csv, output_txt)` -> write namelist file
- `stash_code_to_name(code, csv_path=None)` -> lookup human name for stash code
- `parse_profile_to_human(profiles, profile_type='time')` -> human-readable profiles
"""
from pathlib import Path
import re
import csv
from typing import List, Union, Optional
from .parse_core import classify_record, BaseSection, Variable
import hashlib


def _split_blocks(lines: List[str]) -> List[List[str]]:
    # find indices of blocks starting with any [namelist:NAME...] or [!namelist:NAME...]
    # match header lines like: [namelist:umstash_streq(...)] or [namelist:items(34008)] or [namelist:ancilcta]
    starts = [i for i, L in enumerate(lines) if re.match(r"^\[!?\s*namelist:[^\]]+\]", L)]
    if not starts:
        return []
    ends = starts[1:] + [len(lines)]
    return [lines[s:e] for s, e in zip(starts, ends)]


def parse_namelist(input_src: Union[str, Path], print_summary: bool = False) -> List[BaseSection]:
    """Parse a namelist text or file into classified section objects.

    Parameters
    ----------
    input_src : str or pathlib.Path
        Path to a namelist file, or a string containing the namelist text.
    print_summary : bool, optional
        If True, print a brief summary of parsed section counts (default False).

    Returns
    -------
    list of BaseSection
        A list of section objects (instances of subclasses of ``BaseSection``).

    Notes
    -----
    Only namelist sections with types ``umstash_use``, ``umstash_time``,
    ``umstash_domain``, ``umstash_streq`` and ``nlstcall_pp`` are processed.
    """
    if isinstance(input_src, (str, Path)):
        p = Path(input_src)
        if p.exists():
            text = p.read_text()
        else:
            # treat as literal text
            text = str(input_src)
    else:
        text = str(input_src)

    lines = [ln.strip() for ln in text.splitlines()]
    blocks = _split_blocks(lines)
    records = []
    
    # Allowed namelist types
    allowed_types = {'umstash_use', 'umstash_time', 'umstash_domain', 'umstash_streq', 'nlstcall_pp'}
    
    for block in blocks:
        header = block[0]
        # extract section name (text after 'namelist:' up to '(' or ']' )
        sect_m = re.match(r"^\[!?\s*namelist:([^\(\]]+)", header)
        section_type = sect_m.group(1).strip() if sect_m else None
        
        # Skip blocks not in allowed types
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
            # continuation line starting with '=' appends to previous key
            if line.lstrip().startswith('='):
                cont = line.lstrip()[1:].strip().strip("'")
                if last_key and last_key in rec:
                    prev = '' if rec.get(last_key) is None else str(rec.get(last_key))
                    # avoid duplicate commas
                    if prev.endswith(',') or cont.startswith(','):
                        new = prev + cont.lstrip(',')
                    elif prev == '':
                        new = cont
                    else:
                        new = prev + ',' + cont
                    rec[last_key] = new
                # if no last_key, ignore continuation
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


def generate_namelist_from_csv(input_src: Union[str, Path, List[BaseSection]], output_txt: str):
    """Write a namelist file from CSV rows or parsed section objects.

    Parameters
    ----------
    input_src : str or pathlib.Path or list of BaseSection
        If a CSV path is provided, the CSV is read and converted to
        ``umstash_streq`` sections (fields expected: ``ISEC``, ``ITEM``,
        ``DOM PROFILE``, ``USE``, ``PACKAGE``, ``TIME PROFILE``).
        If a list of parsed section objects (as returned by
        ``parse_namelist``) is provided, those sections are written verbatim
        (header, id and record values preserved where possible).
    output_txt : str
        Path to the output namelist text file to write.

    Returns
    -------
    None
    """

    def generate_suffix(isec, item, dom_name, tim_name):
        """Generate a unique suffix based on section parameters."""
        data = f"{isec}:{item}:{dom_name}:{tim_name}".encode()
        return hashlib.sha256(data).hexdigest()[:8]

    def _write_sections(sections: List[BaseSection], out_path: str):
        # map dataclass types to namelist section names when record doesn't contain one
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

                # build header
                if sid:
                    out.write(f"[{'!' if not incl else ''}namelist:{sect_name}({sid})]\n")
                else:
                    out.write(f"[{'!' if not incl else ''}namelist:{sect_name}]\n")
                # write record keys (skip 'section', 'id', 'incl' as redundant)
                def _wrap_comma_separated_numbers(s: str, first_prefix: str, cont_prefix: str, max_width: int = 72):
                    # split into items and drop empty items
                    items = [it.strip() for it in re.split(r',\s*', s) if it and it.strip()]
                    if not items:
                        return [f"{first_prefix}"]
                    lines = []
                    cur_items = []
                    prefix = first_prefix
                    for idx, it in enumerate(items):
                        # try adding this item to current chunk
                        attempt = cur_items + [it]
                        joined = ','.join(attempt)
                        if len(prefix) + len(joined) <= max_width:
                            cur_items = attempt
                        else:
                            # emit current chunk (add trailing comma if there are remaining items)
                            if cur_items:
                                remaining = len(items) - (idx)
                                line = prefix + ','.join(cur_items)
                                if remaining > 0 and not line.endswith(','):
                                    line = line + ','
                                lines.append(line)
                            # start new chunk with this item using continuation prefix
                            prefix = cont_prefix
                            cur_items = [it]
                    # emit final chunk
                    if cur_items:
                        line = prefix + ','.join(cur_items)
                        # do not add trailing comma to final overall line
                        lines.append(line)
                    return lines

                for key, value in (section.record or {}).items():
                    if key in ('section', 'id', 'incl'):
                        continue
                    # do not write variable_name into variable (umstash_streq) sections
                    if key == 'variable_name' and sect_name == 'umstash_streq':
                        continue
                    s = '' if value is None else str(value)
                    # strip surrounding quotes left from parsing
                    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                        s = s[1:-1]
                    s = s.strip()

                    low = s.lower()
                    # Fortran-style booleans
                    if low in ('.true.', '.false.'):
                        out.write(f"{key}={low}\n")
                        continue
                    if low in ('true', 't'):
                        out.write(f"{key}=.true.\n")
                        continue
                    if low in ('false', 'f'):
                        out.write(f"{key}=.false.\n")
                        continue

                    # comma-separated numeric lists (integers or floats)
                    if re.match(r'^-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)*\s*$', s):
                        # Clean items (drop empty entries) and write as a single unquoted comma list
                        items = [it.strip() for it in re.split(r',\s*', s) if it and it.strip()]
                        joined = ','.join(items)
                        out.write(f"{key}={joined}\n")
                        continue

                    # plain number (int/float)
                    if re.match(r'^-?\d+(?:\.\d+)?$', s):
                        out.write(f"{key}={s}\n")
                        continue

                    # default: quote string
                    out.write(f"{key}='{s}'\n")
                out.write('\n')

    # If input_src is a list of sections, write them directly
    if isinstance(input_src, (list, tuple)):
        _write_sections(list(input_src), output_txt)
        return None

    # otherwise assume a CSV path
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
   



def parse_profile_to_human(profiles: List[str], profile_type: str = 'time') -> List[str]:
    """Convert a list of profile identifiers into human-readable strings.

    Parameters
    ----------
    profiles : list of str
        List of profile identifiers to convert (e.g. names used in namelists).
    profile_type : str, optional
        Profile type to interpret (currently only ``'time'`` is used).

    Returns
    -------
    list of str
        Human-friendly profile names (title-cased and cleaned).
    """
    out = []
    for p in profiles:
        if p is None:
            out.append('')
            continue
        s = str(p).strip().strip("'")
        s = s.replace('_', ' ')
        out.append(s.title())
    return out


def stash_code_to_name(obj_or_code: Union[str, List[Union[str, BaseSection]]], csv_path: Optional[Union[str, Path]] = None):
    """Lookup human-readable variable names for STASH codes.

    Parameters
    ----------
    obj_or_code : str or list of (str or BaseSection)
            - If a string (e.g. ``'m01s00i003'`` or a URI containing this token),
                the function returns the matching human label or ``None``.
            - If a list of strings or BaseSection objects is provided, the
                function returns a list of labels (or ``None`` for missing matches).
                When BaseSection objects are given, the function will attempt to
                augment each object in-place by setting ``record['variable_name']``
                and ``obj.variable_name`` when a match is found.
    csv_path : str or pathlib.Path, optional
            Path to a STASH codes CSV to use for lookups. If omitted the function
            tries to locate ``examples/stash_codes.csv`` inside the package.

    Returns
    -------
    str or list
            If a single string was passed in, returns a single label or ``None``.
            If a list was passed, returns a list of labels (or ``None`` entries).
    """
    # helper: locate CSV
    def _locate_csv(path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        if path:
            p = Path(path)
            if p.exists():
                return p
        # try common locations relative to package
        here = Path(__file__).resolve()
        pkg_root = here.parents[2] if len(here.parents) >= 3 else here.parent
        candidates = [pkg_root / 'examples' / 'stash_codes.csv', pkg_root / 'examples' / 'stash_codes.csv', here.parent / 'stash_codes.csv']
        for c in candidates:
            if c.exists():
                return c
        return None

    csv_file = _locate_csv(csv_path)

    # build mapping: short token (m01s00i003) -> label
    mapping = {}
    token_re = re.compile(r"m\d{1,2}s\d{1,2}i\d{1,3}", re.IGNORECASE)

    if csv_file:
        try:
            with open(csv_file, newline='') as f:
                reader = csv.DictReader(f)
                # try to locate common columns
                fieldnames = [fn.lower() for fn in (reader.fieldnames or [])]
                notation_col = None
                label_col = None
                for i, fn in enumerate(fieldnames):
                    if 'skos:notation' in fn or 'notation' in fn:
                        notation_col = reader.fieldnames[i]
                    if 'rdfs:label' in fn or 'label' in fn:
                        label_col = reader.fieldnames[i]

                for row in reader:
                    # obtain label
                    label = None
                    if label_col and row.get(label_col):
                        label = row.get(label_col).strip()
                    else:
                        # fallback to last non-empty column value
                        for v in reversed(list(row.values())):
                            if v and str(v).strip():
                                label = str(v).strip()
                                break

                    # obtain token
                    token = None
                    if notation_col and row.get(notation_col):
                        token_val = row.get(notation_col)
                        if token_val:
                            m = token_re.search(token_val)
                            token = m.group(0).lower() if m else token_val.strip().lower()
                    if not token:
                        # try to find a token anywhere in the row
                        for v in row.values():
                            if not v:
                                continue
                            m = token_re.search(str(v))
                            if m:
                                token = m.group(0).lower()
                                break

                    if token and label:
                        mapping[token] = label
        except Exception:
            # fall through with empty mapping
            mapping = {}

    # normalise single-code lookup
    def _lookup_code(code: str) -> Optional[str]:
        if not code:
            return None
        code = str(code).strip()
        m = token_re.search(code)
        key = m.group(0).lower() if m else code.lower()
        return mapping.get(key)

    # handle single string
    if isinstance(obj_or_code, str):
        return _lookup_code(obj_or_code)

    # handle iterable
    out = []
    for item in obj_or_code:
        # string item
        if isinstance(item, str):
            out.append(_lookup_code(item))
            continue

        # object/dict-like: try to read isec/item from record
        rec = None
        if hasattr(item, 'record') and isinstance(item.record, dict):
            rec = item.record
        elif isinstance(item, dict):
            rec = item

        if not rec:
            out.append(None)
            continue

        isec = rec.get('isec') or rec.get('ISEC') or rec.get('s') or rec.get('section')
        itm = rec.get('item') or rec.get('ITEM') or rec.get('i')
        try:
            isec_i = int(isec)
        except Exception:
            isec_i = None
        try:
            item_i = int(itm)
        except Exception:
            item_i = None

        if isec_i is None or item_i is None:
            out.append(None)
            continue

        short = f"m01s{isec_i:02d}i{item_i:03d}"
        name = mapping.get(short.lower()) or mapping.get(short)
        if name:
            # update record and object attribute when possible
            rec['variable_name'] = name
            try:
                setattr(item, 'variable_name', name)
            except Exception:
                pass
        out.append(name)

    return out


__all__ = [
    'parse_namelist',
    'generate_namelist_from_csv',
    'stash_code_to_name',
    'parse_profile_to_human',
]
