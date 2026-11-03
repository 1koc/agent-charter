#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 agent-charter 的骨架铺到目标仓库。

决策（为什么这么写）：
- **默认不覆盖**：目标可能已有 AGENTS.md / index.md 且含真实项目事实，
  覆盖一次就丢掉用户积累的规则，且无法从本脚本恢复 ⇒ 覆盖必须显式 --force。
- **不删任何文件**：本脚本只做「新建」和「创建空目录」，不做清理。
  清理属破坏性动作，须由人逐次授权（见 index.md §1.8）。
- **--dry-run 输出完整清单**：铺之前先看清会写哪些路径，
  避免在错误目录（如用户家目录）铺一堆文件。
- **空目录也建**：doc/archive 等目录若不存在，AI 会以为「没有归档惯例」
  而把方案散放根目录；目录本身就是规则的一部分。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TPL = SKILL_ROOT / "templates"

# 骨架里需要存在、但模板中没有文件的空目录（目录本身即规则的一部分）
EMPTY_DIRS = [
    "doc/archive",
    "doc/research",
    "doc/note",
    "doc/bug",
    "doc/chaos",
    "doc/origin",
    "doc/collect",
]

MINIMAL_FILES = ["AGENTS.md", "index.md"]


def _collect_plan(minimal: bool) -> list[tuple[Path, Path]]:
    """返回 [(模板文件, 目标相对路径)] 列表。"""
    plan: list[tuple[Path, Path]] = []
    for name in MINIMAL_FILES:
        plan.append((TPL / name, Path(name)))
    if not minimal:
        for src in sorted(TPL.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(TPL)
            if str(rel) in MINIMAL_FILES:  # 已在上面加过
                continue
            plan.append((src, rel))
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(
        description="把 AI 协作框架骨架铺到目标仓库（幂等，默认不覆盖）"
    )
    ap.add_argument("target", nargs="?", default=".", help="目标仓库根目录（默认当前目录）")
    ap.add_argument(
        "--minimal", action="store_true", help="只铺 AGENTS.md + index.md（档 0）"
    )
    ap.add_argument("--force", action="store_true", help="覆盖已存在的文件（慎用）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要写入的路径，不落盘")
    args = ap.parse_args()

    # Windows 控制台默认 GBK，中文路径与提示会乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if not TPL.is_dir():
        print(f"[ERR] 模板目录不存在: {TPL}")
        return 2

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"[ERR] 目标目录不存在（请先创建，本脚本不建目标根）: {target}")
        return 2

    plan = _collect_plan(args.minimal)

    created: list[str] = []
    skipped: list[str] = []
    overwritten: list[str] = []

    def handle(src: Path, rel: Path) -> None:
        dst = target / rel
        label = rel.as_posix()
        exists = dst.exists()
        if exists and not args.force:
            skipped.append(label)
            return
        if args.dry_run:
            (overwritten if exists else created).append(label)
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        (overwritten if exists else created).append(label)

    print(f"目标: {target}")
    print(f"模式: {'minimal(档0)' if args.minimal else 'full'} | "
          f"{'DRY-RUN' if args.dry_run else '写入'} | "
          f"{'force(覆盖)' if args.force else 'skip-existing'}")
    print("-" * 60)

    for src, rel in plan:
        handle(src, rel)

    if not args.minimal:
        for d in EMPTY_DIRS:
            p = target / d
            if p.is_dir():
                continue
            if args.dry_run:
                created.append(d + "/")
            else:
                p.mkdir(parents=True, exist_ok=True)
                created.append(d + "/")

    def dump(label: str, items: list[str]) -> None:
        if not items:
            return
        print(f"\n[{label}] {len(items)}")
        for i in items:
            print(f"  {i}")

    dump("新建", created)
    dump("覆盖", overwritten)
    dump("跳过（已存在）", skipped)

    print("-" * 60)
    if args.dry_run:
        print("DRY-RUN 结束，未落盘。去掉 --dry-run 执行。")
        return 0

    print("下一步（必做，否则骨架只是空壳）：")
    print("  1. 逐项填写 index.md 的 §0 填充清单，填完删掉那一节")
    if not args.minimal:
        print("  2. 把 doc/ref/build.md 里每条命令实跑一次，改掉与实况不符的")
        print("  3. 走 SKILL.md 阶段 4 的四条自检")
    else:
        print("  2. 走 SKILL.md 阶段 4 的四条自检（需要 doc/ 骨架时去掉 --minimal 重跑）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
