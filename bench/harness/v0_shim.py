#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright==1.64.0", "faster-whisper==1.2.1", "numpy", "pillow"]
# ///
"""v0_shim.py — run the owner's private solver (<private v0 solver>, "solver v0") unmodified against the
bench's own browser instead of the shared the automation browser.

    uv run --script harness/v0_shim.py --cdp http://127.0.0.1:PORT --log DIR -- solve --url <task url>

captcha.py hard-codes the automation browser (CDP 127.0.0.1:9223) and its shared event log. This loads the file as a
module, points those two constants at the bench's browser and the bench's own log folder, and calls its main()
with the given arguments: same code, same ladder, same exit codes (0 solved, 3 needs eyes, 4 no CAPTCHA, 1 error).
Same dependency pins as captcha.py's own header.
"""
import importlib.util
import os
import sys

V0 = "<private v0 solver>"


def main():
    argv = sys.argv[1:]
    cdp = argv[argv.index("--cdp") + 1]
    log = argv[argv.index("--log") + 1]
    rest = argv[argv.index("--") + 1:]
    spec = importlib.util.spec_from_file_location("captcha_v0", V0)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.CDP = cdp
    os.makedirs(log, exist_ok=True)
    mod.LOG_DIR = log
    mod.LOG = os.path.join(log, "events.jsonl")
    sys.argv = [V0] + rest
    try:
        mod.main()
    except SystemExit:
        raise
    except Exception as e:                 # same last-resort behaviour as captcha.py's own __main__
        import json
        print(json.dumps({"result": "error", "detail": repr(e)[:300]}))
        sys.exit(1)


if __name__ == "__main__":
    main()
