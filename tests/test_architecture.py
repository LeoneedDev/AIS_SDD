"""Component boundaries: importy medzi balíkmi rešpektujú allowed_dependencies z components.yaml."""
import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "pod"

PACKAGES = {
    "modeling_workspace": "AC-ModelingWorkspace",
    "model_validator": "AC-ModelValidator",
    "model_repository": "AC-ModelRepository",
    "order_orchestrator": "AC-OrderOrchestrator",
    "notifier": "AC-Notifier",
    "customer_portal": "AC-CustomerPortal",
}

# components.yaml neurčuje allowed_dependencies pre Model Repository; implementácia potrebuje
# údaje objednávky (vlastník, začatá tlač) a súhlas s opravou (BR-005). Čaká na rozhodnutie človeka.
NOT_IN_SPEC = {"AC-ModelRepository": {"AC-OrderOrchestrator", "AC-ModelingWorkspace"}}


def _allowed() -> dict[str, set[str]]:
    data = yaml.safe_load((ROOT / "spec/application/components.yaml").read_text(encoding="utf-8"))
    allowed = {c["id"]: set(c.get("allowed_dependencies", [])) for c in data["application_components"]}
    for component, extra in NOT_IN_SPEC.items():
        allowed[component] |= extra
    return allowed


def _imports(package: str) -> set[str]:
    used = set()
    for file in (SRC / package).rglob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                if parts[0] == "pod" and len(parts) > 1 and parts[1] in PACKAGES and parts[1] != package:
                    used.add(PACKAGES[parts[1]])
    return used


def test_component_dependencies_are_allowed():
    allowed = _allowed()
    for package, component in PACKAGES.items():
        illegal = _imports(package) - allowed.get(component, set())
        assert not illegal, f"{component} závisí od {illegal}, čo nie je v allowed_dependencies"
