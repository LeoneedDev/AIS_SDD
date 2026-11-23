"""Zástupný validátor (reálne tlačiarne nie sú k dispozícii).

Výsledok určujú značky v obsahu súboru:
  STUB:ERROR                    -> failed, model obsahuje chybu
  STUB:TOO_LARGE_UNSPLITTABLE   -> passed, nezmestí sa, slicer ho nevie rozdeliť
  STUB:TOO_LARGE                -> passed, nezmestí sa, slicer ho vie rozdeliť
  inak                          -> passed, zmestí sa
"""
from dataclasses import dataclass, field


@dataclass
class StubResult:
    result: str
    errors: list[dict] = field(default_factory=list)
    fits_printer: bool = True
    splittable: bool | None = None


def validate(content: bytes, print_type: str) -> StubResult:
    if b"STUB:ERROR" in content:
        return StubResult("failed", [{"code": "stub_error",
                                      "message": f"Model obsahuje chybu pre typ tlače {print_type} (simulované)."}])
    if b"STUB:TOO_LARGE_UNSPLITTABLE" in content:
        return StubResult("passed", fits_printer=False, splittable=False)
    if b"STUB:TOO_LARGE" in content:
        return StubResult("passed", fits_printer=False, splittable=True)
    return StubResult("passed")
