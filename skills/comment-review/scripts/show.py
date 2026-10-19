import json,sys,subprocess,re
import os
BASE = os.environ.get("COMMENT_REVIEW_BASE") or subprocess.run(
    ["git", "merge-base", "HEAD", "origin/master"], capture_output=True, text=True, check=True).stdout.strip()
d=json.load(open(sys.argv[1])); i=int(sys.argv[2]); x=d[i]
ctx = sys.argv[3] if len(sys.argv)>3 else "8"
diff=subprocess.run(["git","diff",f"-U{ctx}",BASE,"HEAD","--",x['file']],capture_output=True,text=True).stdout
print(f"[{i+1}/{len(d)}] {x['file']}:{x['start']} ({x['status']})")
for h in re.split(r"(?m)^(?=@@ )", diff)[1:]:
    m=re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))?",h); s=int(m.group(1)); n=int(m.group(2) or 1)
    if s<=x['end'] and s+n-1>=x['start']:
        # print with new-file line numbers, trimming to window around comment
        ln=s; out=[]
        for l in h.split("\n")[1:]:
            if not l: continue
            if l.startswith("-"): out.append((ln,"     "+l)); continue
            out.append((ln,f"{ln:5}{l}")); ln+=1
        lo,hi=x['start']-int(ctx),x['end']+int(ctx)
        for k,t in out:
            if lo<=k<=hi: print(t)
