from __future__ import annotations

import asyncio
import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import Settings
from .dataset.writer import DatasetWriter
from .pipeline.batch import run_batch
from .utils.cache import Cache
from .utils.logging import configure_logging, get_logger

console = Console()
log = get_logger(__name__)


def _load_settings(**overrides) -> Settings:
    kwargs = {k: v for k, v in overrides.items() if v is not None}
    return Settings(**kwargs)


@click.group()
@click.version_option("0.1.0")
def cli() -> None:
    """音声ファイルからFine-tuning用教師データセットを作成するCLI。"""


@cli.command()
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="出力ディレクトリ")
@click.option("--language", "-l", default=None, help="言語コード (例: ja, en)")
@click.option("--concurrency", "-c", type=int, default=None, help="並列処理数")
@click.option("--agree-threshold", type=float, default=None, help="一致とみなす類似度閾値 (0-1)")
@click.option("--review-threshold", type=float, default=None, help="要レビューとみなす類似度閾値 (0-1)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="詳細ログを表示")
def build(
    input: Path,
    output: Path | None,
    language: str | None,
    concurrency: int | None,
    agree_threshold: float | None,
    review_threshold: float | None,
    verbose: bool,
) -> None:
    """音声ファイル（またはディレクトリ）から教師データを生成する。"""
    configure_logging(verbose)

    try:
        settings = _load_settings(
            OUTPUT_DIR=output,
            LANGUAGE=language,
            CONCURRENCY=concurrency,
            SIMILARITY_AGREE_THRESHOLD=agree_threshold,
            SIMILARITY_REVIEW_THRESHOLD=review_threshold,
        )
    except Exception as e:
        console.print(f"[red]設定エラー: {e}[/red]")
        raise SystemExit(1)

    writer = DatasetWriter(settings.output_dir)
    cache = Cache(settings.cache_dir)

    console.print(f"[bold]入力:[/bold] {input}")
    console.print(f"[bold]出力:[/bold] {settings.output_dir}")
    console.print(f"[bold]言語:[/bold] {settings.language} / 並列数: {settings.concurrency}")

    result = asyncio.run(run_batch(input, settings, writer, cache))

    table = Table(title="完了")
    table.add_column("項目")
    table.add_column("件数", justify="right")
    table.add_row("処理ファイル", str(result["total"]))
    table.add_row("書き出しレコード", str(result["written"]))
    table.add_row("失敗ファイル", str(result["failed"]))
    table.add_row("train.jsonl", str(writer.train_path))
    table.add_row("review.jsonl", str(writer.review_path))
    console.print(table)


@cli.command()
@click.argument("jsonl", type=click.Path(exists=True, path_type=Path))
@click.option("--limit", "-n", type=int, default=10, help="表示件数")
def inspect(jsonl: Path, limit: int) -> None:
    """生成したJSONLファイルの内容を確認する。"""
    configure_logging()
    lines = jsonl.read_text(encoding="utf-8").strip().splitlines()

    table = Table(title=str(jsonl))
    table.add_column("ID")
    table.add_column("Strategy")
    table.add_column("Sim", justify="right")
    table.add_column("Conf", justify="right")
    table.add_column("Review")
    table.add_column("Text", no_wrap=False, max_width=60)

    for line in lines[:limit]:
        rec = json.loads(line)
        table.add_row(
            rec["id"],
            rec["source"]["strategy"],
            f"{rec['source']['similarity']:.2f}",
            f"{rec['source']['confidence']:.2f}",
            "✓" if rec["quality"]["needs_review"] else "",
            rec["text"][:80],
        )

    console.print(table)
    console.print(f"\n総レコード数: {len(lines)}")


@cli.command()
@click.argument("jsonl", type=click.Path(exists=True, path_type=Path))
def stats(jsonl: Path) -> None:
    """データセットの統計情報を表示する。"""
    configure_logging()
    lines = jsonl.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(l) for l in lines]

    strategies: dict[str, int] = {}
    needs_review = 0
    total_sim = 0.0

    for r in records:
        s = r["source"]["strategy"]
        strategies[s] = strategies.get(s, 0) + 1
        if r["quality"]["needs_review"]:
            needs_review += 1
        total_sim += r["source"]["similarity"]

    console.print(f"\n[bold]総レコード数:[/bold] {len(records)}")
    console.print(f"[bold]要レビュー:[/bold] {needs_review} ({needs_review/len(records)*100:.1f}%)")
    console.print(f"[bold]平均類似度:[/bold] {total_sim/len(records):.3f}")
    console.print("\n[bold]採用戦略の内訳:[/bold]")
    for s, count in sorted(strategies.items(), key=lambda x: -x[1]):
        console.print(f"  {s}: {count}")
