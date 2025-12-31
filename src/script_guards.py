import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class GuardResult:
    updated_text: str
    warnings: List[str]
    critical: List[str]


_FOREIGN_MINISTER_WRONG_PATTERNS = [
    # Present-tense / role-assertion patterns we want to prevent
    r"\bSveriges\s+utrikesminister\s+Tobias\s+Billström\b",
    r"\butrikesministern\s+Tobias\s+Billström\b",
    r"\butrikesminister\s+Tobias\s+Billström\b",
]


def guard_outdated_foreign_minister(text: str) -> GuardResult:
    """Prevent the script from asserting Tobias Billström is Sweden's foreign minister.

    Strategy:
    - If the script already frames him as *former* ("tidigare"), do nothing.
    - Otherwise, replace the role-assertion phrase with the current minister name.

    This is intentionally narrow to avoid rewriting historical references.
    """
    if not text:
        return GuardResult(updated_text=text, warnings=[], critical=[])

    warnings: List[str] = []
    critical: List[str] = []

    # If it says "tidigare utrikesminister Tobias Billström" we allow it.
    if re.search(r"\btidigare\s+utrikesminister\s+Tobias\s+Billström\b", text, flags=re.IGNORECASE):
        return GuardResult(updated_text=text, warnings=[], critical=[])

    updated = text
    replaced = False

    for pat in _FOREIGN_MINISTER_WRONG_PATTERNS:
        if re.search(pat, updated, flags=re.IGNORECASE):
            replaced = True
            # Use current minister name (as of late 2024+): Maria Malmer Stenergard.
            updated = re.sub(
                pat,
                "Sveriges utrikesminister Maria Malmer Stenergard",
                updated,
                flags=re.IGNORECASE,
            )

    if replaced:
        warnings.append(
            "Korrigerade påstående om utrikesminister: ersatte 'Tobias Billström' med 'Maria Malmer Stenergard'."
        )

    # If Billström appears *together with* the word utrikesminister anywhere else, flag it for manual review.
    if re.search(r"Billström", updated, flags=re.IGNORECASE) and re.search(r"utrikesminister", updated, flags=re.IGNORECASE):
        warnings.append(
            "Noterade att 'Billström' och 'utrikesminister' förekommer i samma manus; dubbelkolla att rollen är korrekt (t.ex. 'tidigare')."
        )

    return GuardResult(updated_text=updated, warnings=warnings, critical=critical)


def apply_all_guards(text: str) -> GuardResult:
    res = guard_outdated_foreign_minister(text)
    return res
