#!/usr/bin/env python3

import base64
import json
import sys
from pathlib import Path


# ── 工具函数 ────────────────────────────────────────────────────

def b64_decode_padded(s: str) -> bytes:
    """自动补齐 padding 后解码 base64（URL-safe / standard 均可）。"""
    s = s.replace("-", "+").replace("_", "/")   # URL-safe → standard
    pad = (4 - len(s) % 4) % 4
    return base64.b64decode(s + "=" * pad)


def parse_vmess(uri: str) -> dict | None:
    """
    解析单条 vmess:// URI。
    成功返回含 id/add/port/ps/net 的字典，失败返回 None。
    """
    prefix = "vmess://"
    if not uri.startswith(prefix):
        return None
    payload = uri[len(prefix):]
    try:
        raw = b64_decode_padded(payload)
        info = json.loads(raw.decode("utf-8"))

        if "Pro" not in info.get("ps",   ""):
            return None

        if "新加坡" not in info.get("ps",   "") and "日本" not in info.get("ps",   "") and "美国" not in info.get("ps",   ""):
            return None

        return {
            "id":   info.get("id",   ""),
            "add":  info.get("add",  ""),
            "port": info.get("port", ""),
            "ps":   info.get("ps",   ""),
            "net":  info.get("net",  ""),
        }
    except Exception as e:
        print(f"  [跳过] 解析失败：{e}", file=sys.stderr)
        return None


# ── 主流程 ──────────────────────────────────────────────────────

def main(filepath: str) -> None:
    path = Path(filepath)
    if not path.exists():
        sys.exit(f"文件不存在：{filepath}")

    # Step 1：读取文件并做外层 base64 解码
    raw_bytes = path.read_bytes().strip()
    try:
        content = b64_decode_padded(raw_bytes.decode("ascii")).decode("utf-8")
        print(f"[信息] 外层 base64 解码成功")
    except Exception:
        # 文件本身不是 base64，直接当文本读
        content = path.read_text(encoding="utf-8")
        print(f"[信息] 文件为纯文本，直接解析")

    # Step 2：逐行筛选 vmess:// 并解析
    lines = content.strip().splitlines()
    print(f"[信息] 共 {len(lines)} 行，开始过滤 vmess:// …\n")

    output = []
    results = []
    for line in lines:
        line = line.strip()
        if not line.startswith("vmess://"):
            continue
        node = parse_vmess(line)
        if node:
            output.append(line)
            results.append(node)

    # Step 3：输出结果
    print(f"{'─'*72}")
    print(f"{'#':<4} {'ps':<60} {'add':<80} {'port':<6} {'net':<6} id")
    print(f"{'─'*72}")
    for i, n in enumerate(results, 1):
        print(
            f"{i:<4} {n['ps'][:50]:<40} {n['add'][:80]:<60} "
            f"{n['port']:<6} {n['net']:<6} {n['id']}"
        )
    print(f"{'─'*72}")
    print(f"[完成] 共提取 {len(results)} 条 vmess 节点\n")

    # Step 4：同时输出 JSON 文件
    out_txt = Path("vmess.txt")
    out_txt.write_text("\n".join(output), encoding="utf-8")
    print(f"[输出] vmess 链接已保存至：{out_txt}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "./gw.txt"
    main(target)
