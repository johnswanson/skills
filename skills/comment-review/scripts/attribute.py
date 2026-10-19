# Attribute each -U0 hunk of the working-tree diff to the branch commit that last touched the lines it replaces,
# and write one patch per commit.
import subprocess, re, sys, os, collections
import os
BASE = os.environ.get("COMMENT_REVIEW_BASE") or subprocess.run(
    ["git", "merge-base", "HEAD", "origin/master"], capture_output=True, text=True, check=True).stdout.strip()
out = sys.argv[1]
def run(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
branch = set(run("git", "rev-list", f"{BASE}..HEAD").split())
order = run("git", "rev-list", "--reverse", f"{BASE}..HEAD").split()
diff = run("git", "diff", "-U0", "HEAD")
patches = collections.defaultdict(list)
report = []
for fdiff in re.split(r"(?m)^(?=diff --git )", diff)[1:]:
    head, *hunks = re.split(r"(?m)^(?=@@ )", fdiff)
    path = re.search(r"^--- a/(.*)$", head, re.M).group(1)
    for h in hunks:
        m = re.match(r"@@ -(\d+)(?:,(\d+))? ", h)
        s, n = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lo, hi = (s, s + n - 1) if n else (s, s)  # pure insertion: blame the line before it
        bl = run("git", "blame", "-l", "-s", "-L", f"{lo},{hi}", "HEAD", "--", path)
        shas = {l.split()[0].lstrip("^") for l in bl.splitlines()}
        mine = [c for c in order if c in shas]
        if not mine:
            report.append(f"UNATTRIBUTED {path}:{s}")
            continue
        target = mine[-1]
        patches[target].append((head, h))
        if len(mine) > 1: report.append(f"multi {path}:{s} -> {target[:10]} (also {[c[:10] for c in mine[:-1]]})")
os.makedirs(out, exist_ok=True)
for c, items in patches.items():
    byfile = collections.OrderedDict()
    for head, h in items: byfile.setdefault(head, []).append(h)
    with open(f"{out}/{order.index(c):02}-{c[:10]}.patch", "w") as f:
        for head, hs in byfile.items(): f.write(head + "".join(hs))
    print(order.index(c), c[:10], len(items), "hunks")
print("\n".join(report))
