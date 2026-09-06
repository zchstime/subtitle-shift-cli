import argparse, re
from pathlib import Path

TIME=re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
def seconds(text):
 h,m,s,ms=map(int,TIME.fullmatch(text).groups()); return h*3600+m*60+s+ms/1000
def stamp(value):
 value=max(0,value); ms=round(value*1000); h,rem=divmod(ms,3600000); m,rem=divmod(rem,60000); s,ms=divmod(rem,1000); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
def parse(text):
 blocks=[]
 for raw in re.split(r"\r?\n\s*\r?\n",text.strip()):
  lines=raw.splitlines()
  if len(lines)<3 or " --> " not in lines[1]: continue
  start,end=lines[1].split(" --> ",1); blocks.append({"index":int(lines[0]),"start":seconds(start),"end":seconds(end),"text":"\n".join(lines[2:])})
 return blocks
def transform(items,shift=0,stretch=1,anchor=0):
 return [{**x,"start":anchor+(x["start"]-anchor)*stretch+shift,"end":anchor+(x["end"]-anchor)*stretch+shift} for x in items]
def validate(items):
 rows=[]
 for a,b in zip(items,items[1:]):
  if a["end"]>b["start"]: rows.append(f"subtitle {a['index']} overlaps {b['index']}")
 for x in items:
  if x["end"]<=x["start"]: rows.append(f"subtitle {x['index']} has non-positive duration")
 return rows
def render(items): return "\n\n".join(f"{i+1}\n{stamp(x['start'])} --> {stamp(x['end'])}\n{x['text']}" for i,x in enumerate(items))+"\n"
def main(argv=None):
 p=argparse.ArgumentParser(description="Shift, stretch, and validate SRT timing"); p.add_argument("srt"); p.add_argument("--shift",type=float,default=0); p.add_argument("--stretch",type=float,default=1); p.add_argument("--anchor",type=float,default=0); p.add_argument("--output","-o",required=True)
 a=p.parse_args(argv); items=transform(parse(Path(a.srt).read_text()),a.shift,a.stretch,a.anchor); Path(a.output).write_text(render(items)); problems=validate(items); print(f"Wrote {len(items)} subtitles"+(f"; warnings: {', '.join(problems)}" if problems else ""))
if __name__=="__main__": main()
