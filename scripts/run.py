import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from langchain_deepseek import ChatDeepSeek  # noqa: E402
from langchain_ollama import ChatOllama  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402

from phish_detector.io_utils import make_output_paths  # noqa: E402
from phish_detector.references import load_references, reference_tag  # noqa: E402
from phish_detector.runner import run_all  # noqa: E402
from phish_detector.workflow import build_workflow  # noqa: E402


DATA_DIR = "datasets/test"
SPLITS = ("malicious", "benign")

_BACKEND_CONFIG: Dict[str, Dict[str, Any]] = {
    "openai": {
        "langchain_project": "openai",
        "parsed_dom_max_chars": 500_000,
    },
    "qwen": {
        "langchain_project": "qwen_3",
        "parsed_dom_max_chars": 15_000,
    },
}


def build_llm(backend: str, serving: str = "sglang"):
    if backend == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            max_retries=2,
        )
    if backend == "qwen":
        if serving == "ollama":
            qwen_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            return ChatOllama(
                model=qwen_model,
                name=qwen_model,
                reasoning=True,
                num_ctx=32768,
            )
        qwen_model = os.getenv("SGLANG_MODEL", "Qwen/Qwen3-8B")
        return ChatDeepSeek(
            model=qwen_model,
            name=qwen_model,
            api_base=os.getenv("SGLANG_API_BASE", "http://127.0.0.1:40000/v1"),
            api_key=os.getenv("SGLANG_API_KEY", "sk-dummy"),  # type: ignore
            max_retries=2,
        )
    raise ValueError(f"unknown backend: {backend!r}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the phishing-detection workflow against the dataset.",
    )
    parser.add_argument(
        "--backend",
        choices=sorted(_BACKEND_CONFIG.keys()),
        required=True,
        help="Which LLM backend to use.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N URLs across all splits (0 = no limit, default).",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help=(
            "Run the full evaluation N times; each cycle writes a separate, "
            "timestamped output file under results/<backend>/."
        ),
    )
    parser.add_argument(
        "--brand-references",
        default="configs/brand_references_telecommunication.yaml",
        help="YAML file of HIGH-popularity reference brands injected into the brand-analyzer prompt as scale anchors.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Enable LangSmith tracing (requires LANGSMITH_API_KEY in .env). Off by default.",
    )
    serving_group = parser.add_mutually_exclusive_group()
    serving_group.add_argument(
        "--sglang",
        action="store_true",
        help="Serve Qwen via SGLang / vLLM through an OpenAI-compatible API (default for --backend qwen).",
    )
    serving_group.add_argument(
        "--ollama",
        action="store_true",
        help="Serve Qwen via Ollama (only valid with --backend qwen).",
    )
    args = parser.parse_args()

    if args.ollama and args.backend != "qwen":
        parser.error("--ollama is only valid with --backend qwen")

    serving = "ollama" if args.ollama else "sglang"

    cfg = _BACKEND_CONFIG[args.backend]
    if args.trace:
        if not os.getenv("LANGSMITH_API_KEY"):
            parser.error("--trace requires LANGSMITH_API_KEY to be set in .env")
        os.environ["LANGCHAIN_PROJECT"] = cfg["langchain_project"]
        os.environ.setdefault("LANGSMITH_TRACING", "true")

    references = load_references(Path(args.brand_references))
    out_suffix = f"_refs-{reference_tag(args.brand_references)}"

    llm = build_llm(args.backend, serving=serving)
    workflow = build_workflow(
        llm,
        parsed_dom_max_chars=cfg["parsed_dom_max_chars"],
        brand_references=references,
    )

    for cycle in range(args.cycles):
        out_jsonl, out_csv = make_output_paths(args.backend, suffix=out_suffix)
        print(f"=== cycle {cycle + 1}/{args.cycles} → {out_jsonl}")
        run_all(
            workflow,
            out_jsonl=str(out_jsonl),
            out_csv=str(out_csv),
            data_dir=DATA_DIR,
            splits=SPLITS,
            limit=args.limit,
        )


if __name__ == "__main__":
    main()
