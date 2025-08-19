#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def main():
    # Default filename if not provided
    default_file = "results_llm.json"
    json_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(default_file)

    # Ensure file exists
    if not json_path.exists():
        print(f"Error: File '{json_path}' not found.")
        sys.exit(1)

    # Load JSON
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)

    # Pretty-print the entire JSON
    print("\n--- Full JSON Content ---")
    print(json.dumps(data, indent=2))

    # Example: Access and print specific values
    print("\n--- Extracted Values ---")
    odo = data.get("odometer_image", {})
    gas = data.get("gas_pump_image", {})

    print(f"Odometer file: {odo.get('file')}")
    print(f"Trip value: {odo.get('top_value_trip')}")
    print(f"Total mileage: {odo.get('bottom_value_total_mileage')}")

    print(f"Gas pump file: {gas.get('file')}")
    print(f"Dollars: {gas.get('top_value_dollars')}")
    print(f"Gallons: {gas.get('bottom_value_gallons')}")

if __name__ == "__main__":
    main()
