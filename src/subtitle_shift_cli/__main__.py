import argparse, re
from pathlib import Path

TIME=re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")
def seconds(text):
 h,m,s,ms=map(int,TIME.fullmatch(text).groups()); return h*3600+m*60+s+ms/1000
def stamp(value):
 value=max(0,value); ms=round(value*1000); h,rem=divmod(ms,3600000); m,rem=divmod(rem,60000); s,ms=divmod(rem,1000); return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
VTT_TIME = re.compile(r"(?:(\d{2,}):)?([0-5]\d):([0-5]\d)\.(\d{3})")


def vtt_seconds(text):
    match = VTT_TIME.fullmatch(text)
    if not match:
        raise ValueError(f"Invalid WebVTT timestamp: {text}")
    hours, minutes, secs, millis = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000


def parse_vtt(text):
    blocks = re.split(r"\r?\n[ \t]*\r?\n", text.strip())
    if not re.fullmatch(r"WEBVTT(?:[ \t][^\r\n]*)?", blocks[0]):
        raise ValueError("Expected a WEBVTT header followed by a blank line")
    cues = []
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        if re.match(r"^(?:NOTE(?:[ \t]|$)|STYLE$|REGION$)", lines[0]):
            raise ValueError("NOTE, STYLE and REGION blocks are not supported")
        identifier = lines.pop(0) if "-->" not in lines[0] else None
        if not lines or "-->" not in lines[0]:
            raise ValueError("Expected WebVTT cue timing")
        start, tail = lines.pop(0).split("-->", 1)
        parts = tail.split(maxsplit=1)
        if not parts:
            raise ValueError("Expected WebVTT cue end time")
        cues.append({"index": len(cues) + 1, "start": vtt_seconds(start.strip()),
                     "end": vtt_seconds(parts[0]), "text": "\n".join(lines),
                     "identifier": identifier, "settings": parts[1] if len(parts) == 2 else ""})
    return cues


def parse(text):
 text = text.removeprefix("\ufeff")
 if re.match(r"^WEBVTT(?:[\s]|$)", text): return parse_vtt(text)
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
def render_vtt(items):
    blocks = []
    for cue in items:
        start = stamp(cue["start"]).replace(",", ".")
        end = stamp(cue["end"]).replace(",", ".")
        timing = f"{start} --> {end}"
        if cue.get("settings"):
            timing += " " + cue["settings"]
        lines = [cue["identifier"]] if cue.get("identifier") else []
        blocks.append("\n".join([*lines, timing, cue["text"]]))
    return "WEBVTT\n\n" + "\n\n".join(blocks) + ("\n" if blocks else "")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Shift, stretch, and validate SRT or WebVTT timing")
    parser.add_argument("input", type=Path)
    parser.add_argument("--shift", type=float, default=0)
    parser.add_argument("--stretch", type=float, default=1)
    parser.add_argument("--anchor", type=float, default=0)
    parser.add_argument("--output", "-o", required=True, type=Path)
    args = parser.parse_args(argv)
    text = args.input.read_text(encoding="utf-8-sig")
    try:
        cues = parse_vtt(text) if args.input.suffix.lower() == ".vtt" else parse(text)
    except ValueError as error:
        parser.error(str(error))
    items = transform(cues, args.shift, args.stretch, args.anchor)
    output = render_vtt(items) if args.output.suffix.lower() == ".vtt" else render(items)
    args.output.write_text(output, encoding="utf-8")
    problems = validate(items)
    print(f"Wrote {len(items)} subtitles" + (f"; warnings: {', '.join(problems)}" if problems else ""))


if __name__ == "__main__":
    main()
