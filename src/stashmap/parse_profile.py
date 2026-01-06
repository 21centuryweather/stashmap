"""Helpers to convert parsed TimeProfile and DomainProfile objects to
human-friendly strings.

The function accepts either a single object/dict or a list of objects/dicts.
Each item should be either an instance of one of the classes produced by
``parse_namelist()`` (subclasses of ``BaseSection``) or a plain ``dict`` with
the same keys. Only `TimeProfile` and `DomainProfile` are processed; other
items are returned unchanged.

For processed items the function will add a new string field named
``description`` to the object's ``record`` (and as an attribute on the object
when possible) and return the modified item(s).
"""
from typing import Any, List, Union
from .parse_core import BaseSection, TimeProfile, DomainProfile
import re


def _humanize_domain(rec: dict) -> str:

    description = ""

    # Horizontal domain type mapping (IOPA values)
    iopa = rec.get('iopa')
    iopa_int = int(iopa)

    iopa_mapping = {
        1: 'Global',
        2: 'N hemisphere',
        3: 'S hemisphere',
        4: '30–90 N',
        5: '30–90 S',
        6: '0–30 N',
        7: '0–30 S',
        8: '30S–30N',
        9: 'Area specified in whole degrees',
        10: 'Area specified in gridpoints',
    }

    if iopa_int in iopa_mapping:
        iopa_text = iopa_mapping[iopa_int]
        # For area-specified types include limits INTH, ISTH, IWST, IEST if present
        if iopa_int in (9, 10):
            inth = rec.get('inth')
            isth = rec.get('isth')
            iwst = rec.get('iwst')
            iest = rec.get('iest')
            limits = []
            if inth is not None:
                limits.append(f"N={inth}")
            if isth is not None:
                limits.append(f"S={isth}")
            if iwst is not None:
                limits.append(f"W={iwst}")
            if iest is not None:
                limits.append(f"E={iest}")

            description += f"{iopa_text}: {', '.join(limits)}, "
        else:
            description += f"{iopa_text}, "

        # Gridpoint masking options
        if rec.get('imsk') != '1' and rec.get('imsk') is not None:
            imsk_int = int(rec.get('imsk'))

            imsk_mapping = {
                1: 'All points',
                2: 'Land points only',
                3: 'Sea points only',
            }

            imsk_text = imsk_mapping[imsk_int]
            description += f"{imsk_text}, "
        
        # Spatial meaning options
        if rec.get('imn') != '0' and rec.get('imn') is not None:
            imn_int = int(rec.get('imn'))

            imn_mapping = {
                0: 'None',
                1: 'Vertical',
                2: 'Zonal',
                3: 'Meridional',
                4: 'Horizontal',
            }

            imn_text = imn_mapping[imn_int]
            description += f"{imn_text} average, "

    # Vertical domain type mapping (IOPL values)
    iopl = rec.get('iopl')
    iopl_int = int(iopl)
    
    iopl_mapping = {
        1: 'Model rho levels',
        2: 'Model theta levels',
        3: 'Pressure levels',
        4: 'Geometric height levels',
        5: 'Single level',
        6: 'Deep soil levels',
        7: 'Potential temperature levels',
        8: 'Potential vorticity levels',
        9: 'Cloud threshold levels',
    }

    if iopl_int in iopl_mapping:
        iopl_text = iopl_mapping[iopl_int]
        # For area-specified types include limits INTH, ISTH, IWST, IEST if present
        if iopl_int in (1, 2, 6):
            ilevs = rec.get('ilevs')
            if int(ilevs) == 1:
                levb = rec.get('levb')
                levt = rec.get('levt')
                #n_levels = int(levt) - int(levb) + 1
                description += f"{iopl_text}: levels {levb} to {levt}"
            if int(ilevs) == 2:
                levlst = rec.get('levlst')
                description += f"{iopl_text}: levels {levlst}, "
        elif iopl_int == 3:
            rlevlst = rec.get('rlevlst')
            description += f"{iopl_text}: {rlevlst}, "
        else:
            description += f"{iopl_text}, "

        if rec.get('plt') != '0' and rec.get('plt') is not None:

            plt_mapping = {
                0: 'None',
                1: 'SW radiation bands',
                2: 'LW radiation bands',
                3: 'Atmospheric assimilation groups',
                4: 'NA',
                5: 'NA',
                6: 'NA',
                7: 'NA',
                8: 'HadCM2 Sulphate Loading Pattern Index',
                9: 'Land and Vegetation Surface Types',
                10: 'Sea ice categories',
                11: 'Number of land surface tiles x maximum number of snow layers',
                12: 'COSP pseudo level categories for satellite observation simulator project',
                13: 'COSP pseudo level categories for satellite observation simulator project',
                14: 'COSP pseudo level categories for satellite observation simulator project',
                15: 'COSP pseudo level categories for satellite observation simulator project',
                16: 'COSP pseudo level categories for satellite observation simulator project',
            }
            plt_int = int(rec.get('plt'))

            plt_text = plt_mapping[plt_int]


            description += f"{plt_text}, "

    return description

def _singular(text: str, count: int) -> str:
    if count == 1:
        return text[:-1]
    return text

def _humanize_time(rec: dict) -> str:

    description = ""

    # Frequency for processing 
    unit_mapping = {
        1: 'timesteps', 
        2: 'hours', 
        3: 'days', 
        4: 'dump periods',
        5: 'minutes',
        6: 'seconds', 
        7: 'real month',
    }

    ifre = rec.get('ifre')
    unt3 = rec.get('unt3')
    unt3_int = int(unt3)
    unt3_text = _singular(unit_mapping[unt3_int], int(ifre))

    freq_text = f"{ifre} {unt3_text}"

    # Time processing code (ITYP)
    ityp = rec.get('ityp')
    ityp_int = int(ityp)

    ityp_mapping = {
        0: 'Not required by STASH',
        1: 'Instantaneous',
        2: 'Accumulated',
        3: 'Time mean',
        4: 'Append time-series',
        5: 'Maximum',
        6: 'Minimum',
        7: 'Trajectory',
    }

    if ityp_int in ityp_mapping:
        iopa_text = ityp_mapping[ityp_int]

        description += f"{iopa_text} every {freq_text}, "
        # Each ITYP code is associated with specific additional parameters
        if ityp_int in (2, 3):
            # Accumulated or Time mean
            isam = rec.get('isam')
            unt2 = rec.get('unt2')
            unt2_int = int(unt2)
            unt2_text = _singular(unit_mapping[unt2_int], int(isam))
            ioff = rec.get('ioff')

            description += f"using data every {isam} {unt2_text}, starting at {ioff} {unt2_text}, " 



    return description


def describe_profiles(
    profiles: Union[Any, List[Any]], profile_type: str = None
) -> Union[Any, List[Any]]:
    """Attach a human-friendly `human_name` to profile objects.

    Parameters
    ----------
    profiles : object or list
        A single parsed section object (subclass of ``BaseSection``) or a
        dictionary with the same keys, or a list of such items.
    profile_type : str, optional
        Optional hint: 'time' or 'domain'. If omitted the function will
        infer the type from the object/record keys.

    Returns
    -------
    The same item or list of items passed in, with ``description`` added to
    each processed item's `record` and as an attribute when possible.
    """
    single = False
    if not isinstance(profiles, list):
        profiles = [profiles]
        single = True

    out = []
    for item in profiles:
        rec = None
        if isinstance(item, DomainProfile) or isinstance(item, TimeProfile):
            rec = item.record
        elif isinstance(item, dict):
            rec = item
        else:
            # Unknown type: leave unchanged
            out.append(item)
            continue

        # Decide profile type
        ptype = profile_type
        if not ptype:
            if isinstance(item, TimeProfile) or 'tim_name' in rec:
                ptype = 'time'
            elif isinstance(item, DomainProfile) or 'dom_name' in rec:
                ptype = 'domain'

        if ptype == 'time':
            human = _humanize_time(rec)
        elif ptype == 'domain':
            human = _humanize_domain(rec)
        else:
            # Unhandled profile type: skip modification
            out.append(item)
            continue

        # Attach human_name to record and object when possible
        rec['description'] = human
        try:
            setattr(item, 'description', human)
        except Exception:
            pass
        out.append(item)

    return out[0] if single else out


"""Lookup human-readable variable names for STASH codes."""
from pathlib import Path
import re
import csv
from typing import List, Union, Optional
from .parse_core import BaseSection


def describe_variable(obj_or_code: Union[str, List[Union[str, BaseSection]]], csv_path: Optional[Union[str, Path]] = None):
    """Lookup human-readable variable names for STASH codes.

    Parameters
    ----------
    obj_or_code : str or list
        - If a string (e.g. ``'m01s00i003'`` or a URI containing this token),
          the function returns the matching human label or ``None``.
        - If an iterable of strings or parsed section objects is provided, the
          function returns a list of labels (or ``None`` for missing matches).
          When parsed section objects are given, the function will attempt to
          augment each object in-place by setting ``record['variable_name']``
          and ``obj.variable_name`` when a match is found.
    csv_path : str or pathlib.Path, optional
        Path to a STASH codes CSV to use for lookups. If omitted the function
        tries to locate ``examples/stash_codes.csv`` inside the package.

    Returns
    -------
    str or list
        If a single string was passed in, returns a single label or ``None``.
        If an iterable was passed, returns a list of labels (or ``None`` entries).
    """
    def _locate_csv(path: Optional[Union[str, Path]] = None) -> Optional[Path]:
        if path:
            p = Path(path)
            if p.exists():
                return p
        here = Path(__file__).resolve()
        pkg_root = here.parents[2] if len(here.parents) >= 3 else here.parent
        candidates = [pkg_root / 'examples' / 'stash_codes.csv', here.parent / 'stash_codes.csv']
        for c in candidates:
            if c.exists():
                return c
        return None

    csv_file = _locate_csv(csv_path)
    mapping = {}
    token_re = re.compile(r"m\d{1,2}s\d{1,2}i\d{1,3}", re.IGNORECASE)

    if csv_file:
        try:
            with open(csv_file, newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = [fn.lower() for fn in (reader.fieldnames or [])]
                notation_col = None
                label_col = None
                for i, fn in enumerate(fieldnames):
                    if 'skos:notation' in fn or 'notation' in fn:
                        notation_col = reader.fieldnames[i]
                    if 'rdfs:label' in fn or 'label' in fn:
                        label_col = reader.fieldnames[i]
                for row in reader:
                    label = None
                    if label_col and row.get(label_col):
                        label = row.get(label_col).strip()
                    else:
                        for v in reversed(list(row.values())):
                            if v and str(v).strip():
                                label = str(v).strip()
                                break
                    token = None
                    if notation_col and row.get(notation_col):
                        token_val = row.get(notation_col)
                        if token_val:
                            m = token_re.search(token_val)
                            token = m.group(0).lower() if m else token_val.strip().lower()
                    if not token:
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
            mapping = {}

    def _lookup_code(code: str) -> Optional[str]:
        if not code:
            return None
        code = str(code).strip()
        m = token_re.search(code)
        key = m.group(0).lower() if m else code.lower()
        if mapping.get(key) is not None:
            return mapping.get(key) 
        else:
            return "Name not available"

    if isinstance(obj_or_code, str):
        return _lookup_code(obj_or_code)

    out = []
    for item in obj_or_code:
        if isinstance(item, str):
            out.append(_lookup_code(item))
            continue
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
            rec['description'] = name
            try:
                setattr(item, 'description', name)
            except Exception:
                pass
        out.append(name)
    return out
