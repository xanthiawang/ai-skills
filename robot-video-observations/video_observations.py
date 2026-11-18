"""Prepare timestamped video evidence and render source-bound visual annotations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

RELATIONS = {"靠近", "远离", "相对位置稳定", "部位运动", "疑似接触", "可见接触", "分离", "目标随动", "可见形变", "遮挡或无法判断"}


def prepare(video, out):
    with video.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else file_hash(source)
    evidence = out / "visual_evidence"
    if not evidence.exists():
        executable = shutil.which("ffmpeg")
        if not executable:
            raise ValueError("需要 ffmpeg 提取带时间点的原始视频帧")
        with tempfile.TemporaryDirectory(dir=out) as tmp:
            folder = Path(tmp) / "frames"
            folder.mkdir()
            filt = "select=isnan(prev_selected_t)+gte(t-prev_selected_t\\,0.5),showinfo,scale=640:-2"
            cmd = [executable, "-nostdin", "-hide_banner", "-i", str(video), "-map", "0:v:0", "-vf", filt,
                   "-vsync", "vfr", "-q:v", "3", str(folder / "%07d.jpg")]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode:
                raise ValueError("ffmpeg 解码失败：" + proc.stderr[-500:])
            times = re.findall(r"Parsed_showinfo[^\n]*?\bn:\s*\d+\s+pts:\s*-?\d+\s+pts_time:([^\s]+)", proc.stderr)
            files = sorted(folder.glob("[0-9]*.jpg"))
            if not files or len(times) != len(files):
                raise ValueError("解码帧与时间戳数量不一致，请检查视频时间轴")
            manifest = dict(source=str(video.resolve()), sha256=digest, source_mtime_utc=datetime.fromtimestamp(
                video.stat().st_mtime, timezone.utc).isoformat(), filter=filt, clock="decoded video PTS (seconds)",
                frames={f.name: float(t) for f, t in zip(files, times)})
            (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            folder.rename(evidence)
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    if manifest["sha256"] != digest:
        raise ValueError("输出目录属于另一段视频，请使用独立目录")
    return manifest


def file_hash(source):
    digest = hashlib.sha256()
    for chunk in iter(lambda: source.read(1048576), b""):
        digest.update(chunk)
    return digest.hexdigest()


def report(out, manifest):
    frames = manifest["frames"]
    review = out / "visual_review.json"
    lines = ["# 纯视频力效观察", "", f"来源：{manifest['source']}", f"SHA-256：{manifest['sha256']}", "",
             "时间依据为视频呈现时间戳。空间关系按画面平面描述。腕部力、力矩、压力和拉班 Weight 均未知。",
             "", "## 可见运动与对象反应", ""]
    if not review.exists():
        lines.append("待看图。按 visual_evidence/manifest.json 的顺序查看帧，必要时回看原视频。")
    else:
        data = json.loads(review.read_text(encoding="utf-8"))
        if data.get("sha256") != manifest["sha256"] or not isinstance(data.get("events"), list):
            raise ValueError("复核文件需要匹配视频的 sha256 和 events 列表")
        if not data["events"]:
            reason = data.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("没有可记录事件时须给出 reason")
            lines.append(reason)
        for event in data["events"]:
            if not isinstance(event, dict) or not all(isinstance(event.get(k), str) and event[k].strip()
                    for k in ("first", "last", "part", "target", "relation", "evidence")):
                raise ValueError("观察事件缺少有效的帧、部位、参照物、关系或画面证据")
            first, last = event["first"], event["last"]
            if first not in frames or last not in frames or frames[first] > frames[last] or event["relation"] not in RELATIONS:
                raise ValueError("观察事件的帧范围或关系无效")
            for name in (first, last):
                if not (out / "visual_evidence" / name).is_file():
                    raise ValueError("缺少引用帧：" + name)
            lines.append(f"- [{frames[first]:g} 秒](visual_evidence/{first}) 至 [{frames[last]:g} 秒](visual_evidence/{last})"
                         f"　{event['part']}／{event['target']}：{event['relation']}。{event['evidence']}")
    with tempfile.NamedTemporaryFile(mode="w", dir=out, encoding="utf-8", delete=False) as f:
        f.write("\n".join(lines) + "\n")
    os.replace(f.name, out / "visual_report.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.video.is_file():
        parser.exit(1, f"Cannot proceed - required data file not found: {args.video}\n")
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        report(args.out, prepare(args.video, args.out))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"视频观察失败：{exc}\n")
    print(args.out / "visual_report.md")


if __name__ == "__main__":
    main()
