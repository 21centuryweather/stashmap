from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class BaseSection:
    id: Optional[str]
    incl: bool
    record: Dict[str, Any]

    @classmethod
    def from_record(cls, record: Dict[str, Any]):
        return cls(id=record.get("id"), incl=record.get("incl", True), record=record)

    def to_csv_row(self) -> Dict[str, Any]:
        return self.record

    def to_namelist_lines(self) -> List[str]:
        sid = self.id or ""
        header = f"[namelist:umstash_streq({sid})]" if self.incl else f"[!namelist:umstash_streq({sid})]"
        lines = [header]
        for k, v in self.record.items():
            if k in ("id", "incl"):
                continue
            val = v
            if isinstance(val, str) and not val.isnumeric():
                val = f"'{val}'"
            lines.append(f"{k}={val}")
        lines.append("")
        return lines


@dataclass
class Variable(BaseSection):
    pass


@dataclass
class TimeProfile(BaseSection):
    pass


@dataclass
class DomainProfile(BaseSection):
    pass


@dataclass
class UseProfile(BaseSection):
    pass


@dataclass
class OutputStream(BaseSection):
    pass


def classify_record(record: Dict[str, Any]) -> BaseSection:
    # Prefer explicit namelist section names when available
    section = (record.get("section") or "").lower()
    section_map = {
        'umstash_use': UseProfile,
        'umstash_time': TimeProfile,
        'umstash_domain': DomainProfile,
        'umstash_streq': Variable,
        'nlstcall_pp': OutputStream,
    }
    if section in section_map:
        return section_map[section].from_record(record)

    # Fallback: simple heuristic-based classification
    keys = {k.upper() for k in record.keys()}
    if any(k in keys for k in ("TIM_PROFILE", "TIM_NAME", "TIME PROFILE", "TIM_NAME")) or "tim_name" in record:
        return TimeProfile.from_record(record)
    if any(k in keys for k in ("DOM_PROFILE", "DOM_NAME", "DOM PROFILE")) or "dom_name" in record:
        return DomainProfile.from_record(record)
    if any(k in keys for k in ("USE", "USE_NAME")) or "use_name" in record:
        return UseProfile.from_record(record)
    if any(k in keys for k in ("STREAM", "OUTPUT")):
        return OutputStream.from_record(record)
    return Variable.from_record(record)
