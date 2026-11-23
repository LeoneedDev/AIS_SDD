"""Contract tests: implementácia vystavuje presne operations z approved contractov."""
from contract_check import load_contracts

from pod.main import SUB_APPS, build_sub_app


def _implemented():
    found = {}
    for prefix, (title, router) in SUB_APPS.items():
        spec = build_sub_app(title, router).openapi()
        for path, ops in spec["paths"].items():
            for method, op in ops.items():
                found[(prefix, path, method)] = op["operationId"]
    return found


def _contracted():
    expected = {}
    for doc in load_contracts():
        prefix = doc["servers"][0]["url"]
        for path, ops in doc["paths"].items():
            for method, op in ops.items():
                if method != "parameters":
                    expected[(prefix, path, method)] = op["operationId"]
    return expected


def test_all_contracts_are_approved():
    for doc in load_contracts():
        assert doc["info"]["x-sdd"]["status"] == "approved", doc["info"]["title"]
        assert doc["info"]["x-sdd"]["approved_by"], doc["info"]["title"]


def test_implementation_matches_contract_operations():
    assert _implemented() == _contracted()


def test_security_matches_contract():
    expected = {}
    for doc in load_contracts():
        prefix = doc["servers"][0]["url"]
        for path, ops in doc["paths"].items():
            for method, op in ops.items():
                if method != "parameters":
                    expected[(prefix, path, method)] = op.get("security", doc.get("security")) or []
    for prefix, (title, router) in SUB_APPS.items():
        spec = build_sub_app(title, router).openapi()
        for path, ops in spec["paths"].items():
            for method, op in ops.items():
                assert (op.get("security") or []) == expected[(prefix, path, method)], f"{method.upper()} {prefix}{path}"
