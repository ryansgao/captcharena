#!/usr/bin/env python3
"""Rewrite old Zola shortcode syntax in content/*.md to Zola 0.23 components (idempotent).
{% coming() %}…{% end %} → {% <coming> %}…{% </coming> %}; {{ live_summary() }} → {{ <live_summary /> }}."""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site/content")
tok = re.compile(r"\{%\s*(\w+)\(\)\s*%\}|\{%\s*end\s*%\}|\{\{\s*(live_summary|doors)\(\)\s*\}\}")
for p in root.rglob("*.md"):
    text, stack, out, pos = p.read_text(), [], [], 0
    for m in tok.finditer(text):
        out.append(text[pos:m.start()])
        if m.group(1):
            stack.append(m.group(1))
            out.append("\n{%% <%s> %%}\n" % m.group(1))
        elif m.group(2):
            out.append("{{ <%s /> }}" % m.group(2))
        else:
            out.append("\n{%% </%s> %%}\n" % stack.pop())
        pos = m.end()
    out.append(text[pos:])
    new = re.sub(r"\n{3,}", "\n\n", "".join(out))
    if new != text:
        p.write_text(new)
        print("converted", p)
