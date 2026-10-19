import subprocess, re, json, sys
import os
BASE = os.environ.get("COMMENT_REVIEW_BASE") or subprocess.run(
    ["git", "merge-base", "HEAD", "origin/master"], capture_output=True, text=True, check=True).stdout.strip()
def run(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
files = run("git","diff","--name-only",BASE,"HEAD").split()
out = []
for f in files:
    try: text = run("git","show",f"HEAD:{f}")
    except subprocess.CalledProcessError: continue
    lines = text.split("\n")
    diff = run("git","diff","-U0",BASE,"HEAD","--",f)
    added = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
        s = int(m.group(1)); n = int(m.group(2) or 1)
        added.update(range(s, s+n))
    ext = f.rsplit(".",1)[-1]
    # mark comment lines
    iscom = [False]*len(lines)
    if ext in ("clj","cljc","cljs","edn"):
        for i,l in enumerate(lines):
            # a comment at line start, or after an opening bracket/whitespace outside a string
            m = re.search(r"(^|[\s({\[]);", l)
            if m and l[:m.start()].count('"') % 2 == 0: iscom[i]=True
        # docstrings: line starting with whitespace + " after a (def.../ns/defendpoint/defsetting line, or :doc
        i=0
        while i < len(lines):
            l = lines[i]
            st = l.strip()
            starts = False
            if re.match(r'\s*"', l) and i>0 and re.search(r'\((def|ns |mu/def|methodical/def|api.macros/defendpoint|setting/defsetting|deftest)', "\n".join(lines[max(0,i-3):i])):
                starts = True
            m = re.search(r'(:doc|:description|docstring)\s+"', l)
            if m: starts = True
            if starts:
                j=i
                # find end of string
                k = l.index('"', m.end()-1 if m else l.index('"'))
                rest = l[k+1:]
                seg = rest
                while True:
                    # find unescaped quote
                    mm = re.search(r'(?<!\\)"', seg)
                    if mm: break
                    j+=1
                    if j>=len(lines): break
                    seg = lines[j]
                for x in range(i, min(j+1,len(lines))): iscom[x]=True
                i=j+1; continue
            i+=1
    elif ext in ("ts","tsx","js","jsx","css"):
        inblock=False
        for i,l in enumerate(lines):
            s=l.strip()
            if inblock:
                iscom[i]=True
                if "*/" in s: inblock=False
                continue
            if s.startswith("//"): iscom[i]=True
            elif s.startswith("/*") or s.startswith("{/*"):
                iscom[i]=True
                if "*/" not in s: inblock=True
            elif re.search(r"\s//\s", l) and not re.search(r"https?://", l): iscom[i]=True
    elif ext in ("yaml","yml"):
        for i,l in enumerate(lines):
            if re.match(r"\s*#", l) or re.match(r"\s*remarks:", l): iscom[i]=True
    # group contiguous comment lines; keep group if any line added
    i=0
    while i < len(lines):
        if iscom[i]:
            j=i
            while j+1<len(lines) and iscom[j+1]: j+=1
            rng = range(i+1,j+2)
            add = [n for n in rng if n in added]
            if add:
                status = "new" if len(add)==len(rng) else "edited"
                out.append({"file":f,"start":i+1,"end":j+1,"status":status,
                            "text":"\n".join(lines[i:j+1])})
            i=j+1
        else: i+=1
json.dump(out, open(sys.argv[1],"w"), indent=1)
print(len(out))
