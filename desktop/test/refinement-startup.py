#!/usr/bin/env python3
"""macOS CLI integration check. Metadata only; never sends a model turn.

Build the small native driver from RefinementLaunch.swift and
RefinementLaunchProbe.swift, then pass its path with --driver. Uses the existing
saved CLI login by link, without reading, copying or printing its contents.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time


def probe(driver):
    with tempfile.TemporaryDirectory(prefix="snapper-startup-check-") as directory:
        metadata = json.loads(subprocess.check_output([str(driver), directory], text=True))
        env = dict(os.environ)
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL"):
            env.pop(key, None)
        env.update(HOME=metadata["profile"], CODEX_HOME=metadata["codexHome"])
        process = subprocess.Popen(
            [metadata["executable"], *metadata["configArguments"], "app-server", "--stdio"],
            cwd=directory, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0, start_new_session=True,
        )
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        pending = bytearray()
        notifications = []

        def write(message):
            process.stdin.write(json.dumps(message).encode() + b"\n")
            process.stdin.flush()

        def call(identifier, method, params):
            # Hard boundary: this test cannot request generation or tools.
            if method not in {"initialize", "account/read", "skills/list", "thread/start"}:
                raise ValueError("Method outside startup-only check")
            write({"id": identifier, "method": method, "params": params})
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                while b"\n" in pending:
                    line, _, rest = pending.partition(b"\n")
                    pending[:] = rest
                    message = json.loads(line)
                    if message.get("id") == identifier:
                        if "error" in message:
                            raise RuntimeError(method + ": protocol error")
                        return message["result"]
                    if message.get("method"):
                        notifications.append(message["method"])
                if selector.select(0.1):
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError(method + ": server exited")
                    pending.extend(chunk)
            raise TimeoutError(method)

        try:
            call(1, "initialize", {"clientInfo": {"name": "snapper_startup_check", "version": "0.7.0"}, "capabilities": {"experimentalApi": True}})
            write({"method": "initialized", "params": {}})
            account = call(2, "account/read", {"refreshToken": False})
            skills = call(3, "skills/list", {"cwds": [directory], "forceReload": True})
            thread = call(4, "thread/start", {"cwd": directory, "ephemeral": True, "sandbox": "read-only", "approvalPolicy": "on-request"})
            rows = skills.get("data", [])
            result = {
                "saved_account_available": bool(account.get("account")),
                "skill_count": sum(len(row.get("skills", [])) for row in rows),
                "skill_errors": sum(len(row.get("errors", [])) for row in rows),
                "instruction_source_count": len(thread.get("instructionSources", [])),
                "ephemeral": thread.get("thread", {}).get("ephemeral"),
                "turn_started": "turn/started" in notifications,
                "generation_requests_sent": 0,
                "auth_reference_remains_symlink": Path(metadata["codexHome"], "auth.json").is_symlink(),
            }
            result["passed"] = (result["saved_account_available"] and result["skill_count"] == 0
                                and result["skill_errors"] == 0 and result["instruction_source_count"] == 0
                                and result["ephemeral"] and not result["turn_started"]
                                and result["auth_reference_remains_symlink"])
            return result
        finally:
            selector.close()
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            except ProcessLookupError:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--driver", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = []
    for _ in range(3):
        try:
            results.append(probe(args.driver.resolve()))
        except Exception as error:
            # Do not expose stderr, account response, config or selected text.
            results.append({"passed": False, "error_type": type(error).__name__, "generation_requests_sent": 0})
    report = {"scope": "startup-only; not a real AI completion or UI permission test", "runs": results}
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    raise SystemExit(0 if all(item["passed"] for item in results) else 1)
