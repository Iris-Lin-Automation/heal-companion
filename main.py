"""CLI for the healing companion MVP."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from companion.chat.loop import chat_once
from companion.heartbeat.checkin import craft_checkin
from companion.memory.store import MemoryStore

app = typer.Typer(add_completion=False, help="治愈陪伴 MVP — 记得你、接住情绪、偶尔主动找你")
console = Console()


def _client() -> tuple[OpenAI, str, str]:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-xxx"):
        console.print("[red]请先复制 .env.example 为 .env 并填入 OPENAI_API_KEY[/red]")
        raise typer.Exit(1)
    base_url = os.getenv("OPENAI_BASE_URL") or None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    name = os.getenv("COMPANION_NAME", "软软")
    return OpenAI(api_key=api_key, base_url=base_url), model, name


@app.command()
def chat(user_id: str = typer.Option("default", help="用户 ID，各自独立记忆")):
    """进入对话。输入 /bye 退出，/mem 看记忆，/ping 生成一条主动关心。"""
    client, model, name = _client()
    store = MemoryStore(user_id)
    console.print(
        Panel(
            f"我是 [bold]{name}[/bold]。\n"
            "相处方式：先接情绪 → 再给现实小步骤 → 长期记得你的事。\n"
            "命令：/mem  /ping  /bye",
            title="治愈陪伴",
        )
    )
    while True:
        try:
            text = console.input("[bold cyan]你> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n先这样，我记得你。")
            break
        if not text:
            continue
        if text in {"/bye", "/exit", "quit"}:
            console.print("好，去忙你的。我在这儿。")
            break
        if text == "/mem":
            items = store.list_memories()
            console.print(store.format_recall_block(items) if items else "还没有长期记忆。")
            continue
        if text == "/ping":
            msg = craft_checkin(client, model, store, name)
            console.print(f"[magenta]{name}>[/magenta] {msg}")
            store.append_chat_log("assistant", msg)
            continue
        reply = chat_once(client, model, store, text, companion_name=name)
        console.print(f"[magenta]{name}>[/magenta] {reply}")


@app.command()
def ping(user_id: str = typer.Option("default")):
    """单独生成一条主动关心（可挂定时任务）。"""
    client, model, name = _client()
    store = MemoryStore(user_id)
    msg = craft_checkin(client, model, store, name)
    console.print(msg)


@app.command("show-mem")
def show_mem(user_id: str = typer.Option("default")):
    """打印长期记忆。"""
    store = MemoryStore(user_id)
    console.print(store.format_recall_block(store.list_memories()))


if __name__ == "__main__":
    app()
