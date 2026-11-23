"""Overenie odpovedí API voči approved contractom (spec/contracts/approved)."""
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DIR = ROOT / "spec" / "contracts" / "approved"


def load_contracts() -> list[dict]:
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(CONTRACT_DIR.glob("*.yaml"))]


def _template_regex(template: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\{[^/]+\}", "[^/]+", template) + "$")


class ContractIndex:
    def __init__(self):
        self.entries = []
        for doc in load_contracts():
            prefix = doc["servers"][0]["url"]
            for template, ops in doc["paths"].items():
                for method, op in ops.items():
                    if method == "parameters":
                        continue
                    self.entries.append((prefix, _template_regex(template), method.upper(), op, doc))

    def find(self, method: str, url_path: str):
        for prefix, regex, m, op, doc in self.entries:
            if m == method and url_path.startswith(prefix) and regex.match(url_path[len(prefix):]):
                return op, doc
        return None, None

    def check(self, method: str, url_path: str, status: int, body) -> None:
        op, doc = self.find(method, url_path)
        if op is None:
            return
        responses = op["responses"]
        assert str(status) in responses, (
            f"{op['operationId']}: status {status} nie je v contracte ({sorted(responses)}); body={body}")
        response = responses[str(status)]
        if "$ref" in response:
            response = doc["components"]["responses"][response["$ref"].split("/")[-1]]
        content = response.get("content", {})
        if not content:
            return
        schema = next(iter(content.values()))["schema"]
        validator = Draft202012Validator({**doc, **schema})
        errors = sorted(validator.iter_errors(body), key=str)
        assert not errors, f"{op['operationId']} {status}: odpoveď nezodpovedá contractu: {errors[0].message}"
