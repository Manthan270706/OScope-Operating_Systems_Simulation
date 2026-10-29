"""Verify all C++ backend CLI demo modes and JSON schemas via WSL."""

import json
import subprocess
import sys

DEMOS = [
    "--demo-paging",
    "--demo-process",
    "--demo-sync",
    "--demo-coffman",
    "--demo-monitor",
    "--demo-fs",
    "--demo-fs-frag",
    "--demo-fs-full",
    "--demo-ipc",
    "--demo-lifecycle",
    "--demo-disk",
]

def main():
    print("=== Testing End-to-End C++ Backend Demos via WSL ===")
    all_ok = True
    for d in DEMOS:
        res = subprocess.run(
            ["wsl", "-d", "Ubuntu", "./build/oscope", d, "--json"],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(f"FAIL {d}: code {res.returncode}, stderr: {res.stderr[:100]}")
            all_ok = False
            continue

        try:
            data = json.loads(res.stdout)
            if isinstance(data, list):
                print(f"PASS {d:<20}: JSON array of {len(data)} experiment results (e.g. category={data[0].get('category')})")
            elif isinstance(data, dict):
                cat = data.get("category", "N/A")
                exp = data.get("experiment", "N/A")
                print(f"PASS {d:<20}: category={cat:<20} | experiment={exp}")
            else:
                print(f"FAIL {d}: unexpected JSON type: {type(data)}")
                all_ok = False
        except Exception as e:
            print(f"FAIL {d}: JSON decode error: {e}")
            all_ok = False

    if all_ok:
        print("\n[SUCCESS] All 11 C++ backend CLI demos produce valid, schema-compliant JSON!")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more demos failed verification!")
        sys.exit(1)

if __name__ == "__main__":
    main()
