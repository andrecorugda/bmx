import subprocess, sys, html
name = sys.argv[1]
out = subprocess.run(["./bmxrender", name + ".bmx"], capture_output=True, text=True).stdout.strip()
src = open(name + ".bmx").read().rstrip()
tpl = """<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
 *{box-sizing:border-box} body{margin:0;background:#eef1f5;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#16181d}
 .wrap{max-width:940px;margin:0 auto;padding:26px 22px}
 .pair{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
 .panel{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(16,24,40,.08),0 8px 24px rgba(16,24,40,.06);overflow:hidden}
 .cap{font:600 11px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.09em;text-transform:uppercase;color:#6b7280;padding:12px 16px;border-bottom:1px solid #eceff3;background:#fafbfc}
 .cap.bad{color:#b42318;background:#fef3f2;border-bottom-color:#fee4e2}
 pre{margin:0;padding:16px;font:13px/1.65 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;color:#1f2937}
 .err{padding:18px;font:13px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;color:#b42318}
 .note{padding:0 18px 18px;color:#5b6270;font-size:14px}
</style></head><body><div class="wrap"><div class="pair">
<div class="panel"><div class="cap">%s.bmx</div><pre>%s</pre></div>
<div class="panel"><div class="cap bad">refused</div><div class="err">%s</div>
<div class="note">Nothing renders. Markdown would have shipped this page with two stray asterisks in it.</div></div>
</div></div></body></html>"""
open(name + ".html","w").write(tpl % (name, html.escape(src), html.escape(out)))
print("wrote", name + ".html")
