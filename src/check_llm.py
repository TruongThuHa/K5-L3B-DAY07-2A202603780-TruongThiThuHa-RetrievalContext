"""Bước D1 · Kiểm tra key LLM (không in key ra màn hình).

    python -m src.check_llm      # lần 1: liệt kê model; lần 2 (đã điền LLM_MODEL): thử gọi tool
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)
    key = os.getenv("LLM_API_KEY", "").strip()
    if not key:
        raise SystemExit("Chưa có LLM_API_KEY trong file .env (nhớ Cmd + S sau khi dán key)")
    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL") or None, timeout=60)

    names = sorted(m.id.removeprefix("models/") for m in client.models.list())
    print("Key hợp lệ. Các model Gemini 'flash' dùng được:")
    for name in names:
        if "flash" in name and "image" not in name and "tts" not in name and "audio" not in name:
            print("   ", name)

    model = os.getenv("LLM_MODEL", "").strip()
    if not model:
        print("\n-> Chọn 1 tên ở trên, điền sau LLM_MODEL= trong .env, Cmd + S, rồi chạy lại lệnh này.")
        return
    tool = {"type": "function", "function": {
        "name": "search_documents", "description": "Search the report for evidence.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}
    resp = client.chat.completions.create(
        model=model, tools=[tool],
        messages=[{"role": "user", "content": "Use the search_documents tool to look up the share of female students."}])
    calls = resp.choices[0].message.tool_calls or []
    if not calls:
        raise SystemExit(f"Model {model} trả lời nhưng KHÔNG gọi tool. Thử model khác trong danh sách.")
    print(f"\nOK: {model} gọi tool {calls[0].function.name} với tham số {json.loads(calls[0].function.arguments)}")
    if resp.usage:
        print(f"Token: vào {resp.usage.prompt_tokens}, ra {resp.usage.completion_tokens}")


if __name__ == "__main__":
    main()