"""CLI del servicio ML independiente."""

from __future__ import annotations

import argparse
import json

from nyc_taxi_ml.config import load_config
from nyc_taxi_ml.modeling import train_demand_models
from nyc_taxi_ml.service import serve


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tfm-ml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train")
    train.add_argument("--mode", choices=("demo", "full"), default="demo")
    service = subparsers.add_parser("serve")
    service.add_argument("--host", default="0.0.0.0")
    service.add_argument("--port", type=int, default=8081)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "serve":
        serve(args.host, args.port)
        return 0
    result = train_demand_models(load_config(), args.mode)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0
