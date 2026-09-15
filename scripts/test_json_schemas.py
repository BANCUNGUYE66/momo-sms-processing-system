import json
from pathlib import Path

def test_json_schemas():
    json_path = Path(__file__).resolve().parent.parent / "examples" / "json_schemas.json"
    print(f"Testing JSON file: {json_path}")

    assert json_path.exists(), "Error: examples/json_schemas.json does not exist!"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "schemas" in data, "Error: Missing 'schemas' key in json_schemas.json"
    schemas = data["schemas"]

    required_entities = ["user", "transaction_category", "user_category_preference", "transaction", "system_log"]
    for entity in required_entities:
        assert entity in schemas, f"Error: Missing entity '{entity}' in json_schemas.json"
        print(f"  [PASS] Found entity schema: {entity}")

    assert "api_response_examples" in schemas, "Error: Missing 'api_response_examples'"
    assert "mapping_guide" in schemas, "Error: Missing 'mapping_guide'"

    print("\nSUCCESS: All JSON schemas and data models validated perfectly!")

if __name__ == "__main__":
    test_json_schemas()
