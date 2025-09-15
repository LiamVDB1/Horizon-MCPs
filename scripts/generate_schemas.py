from __future__ import annotations

import os
import re
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from typing import Iterable, List, Tuple

import requests
import typer


app = typer.Typer(add_completion=False)


def _run_codegen(input_path: str, output_path: str) -> None:
    cmd = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input-file-type",
        "openapi",
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--openapi-scopes",
        "schemas",
        "paths",
        "parameters",
        "--use-title-as-name",
        #"--reuse-model", # this is causing crashes for `token.v2.yaml`, something with schema inherits (allOf) from a schema that's an array.
        "--use-field-description",
        "--collapse-root-models",
        "--allow-extra-fields",
        "--disable-timestamp",
        "--target-python-version",
        "3.12",
        "--enum-field-as-literal",
        "one",
        "--input",
        input_path,
        "--output",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def _sanitize_base(name: str) -> str:
    base = name.replace(".", "_").replace("-", "_")
    base = re.sub(r"[^0-9A-Za-z_]+", "_", base)
    return base


def _local_inputs(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    exts = {".yaml", ".yml", ".json"}
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def _gh_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _parse_github(url: str) -> Tuple[str, str, str | None, str, str]:
    u = urlparse(url)
    host = u.netloc
    parts = [p for p in u.path.strip("/").split("/") if p]
    if host == "raw.githubusercontent.com":
        owner, repo, branch, *rest = parts
        return owner, repo, branch, "/".join(rest), "file"
    if host == "github.com":
        owner, repo, *rest = parts
        if not rest:
            return owner, repo, None, "", "repo"
        kind = rest[0]
        if kind in {"blob", "tree"}:
            branch = rest[1] if len(rest) > 1 else None
            path = "/".join(rest[2:]) if len(rest) > 2 else ""
            return owner, repo, branch, path, ("file" if kind == "blob" else "dir")
        return owner, repo, None, "/".join(rest), "repo"
    raise ValueError("Not a GitHub URL")


def _github_default_branch(owner: str, repo: str) -> str:
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=_gh_headers(), timeout=20)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


def _github_dir_files(owner: str, repo: str, path: str, ref: str) -> List[Tuple[str, str]]:
    # returns list of (download_url, filename)
    out: List[Tuple[str, str]] = []
    def walk(p: str) -> None:
        api = f"https://api.github.com/repos/{owner}/{repo}/contents/{p}" + (f"?ref={ref}" if ref else "")
        resp = requests.get(api, headers=_gh_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("type") == "file":
            out.append((data["download_url"], data["name"]))
            return
        for item in data:
            t = item.get("type")
            name = item.get("name", "")
            if t == "dir":
                walk(item.get("path", ""))
            elif t == "file" and any(name.lower().endswith(ext) for ext in (".yaml", ".yml", ".json")):
                out.append((item.get("download_url"), name))
    walk(path or "")
    return out


def _download(url: str, dst: Path) -> None:
    r = requests.get(url, headers=_gh_headers(), timeout=60)
    r.raise_for_status()
    dst.write_bytes(r.content)


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


@app.command()
def gen(input: str, output: str) -> None:
    """Generate Pydantic schemas from OpenAPI.

    INPUT: local file/dir or GitHub URL (blob/tree/raw)
    OUTPUT: file path (for single input) or directory (for multiple)
    """
    in_is_url = input.startswith("http://") or input.startswith("https://")
    out_path = Path(output)
    if in_is_url and ("github.com" in input or "raw.githubusercontent.com" in input):
        owner, repo, branch, path, kind = _parse_github(input)
        if not branch and kind != "file":
            branch = _github_default_branch(owner, repo)
        if kind == "file":
            raw = input if input.startswith("https://raw.githubusercontent.com/") else f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            with tempfile.TemporaryDirectory() as td:
                tmp_in = Path(td) / Path(path).name
                _download(raw, tmp_in)
                if out_path.suffix == ".py":
                    _ensure_dir(out_path)
                    _run_codegen(str(tmp_in), str(out_path))
                else:
                    out_file = out_path / f"{_sanitize_base(Path(path).stem)}.py"
                    _ensure_dir(out_file)
                    _run_codegen(str(tmp_in), str(out_file))
            return
        # directory/repo
        files = _github_dir_files(owner, repo, path, branch or "main")
        if out_path.suffix == ".py":
            raise typer.BadParameter("Output must be a directory when processing multiple files")
        out_path.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            failures: List[str] = []
            for download_url, name in files:
                if not any(name.lower().endswith(ext) for ext in (".yaml", ".yml", ".json")):
                    continue
                try:
                    tmp_in = Path(td) / name
                    _download(download_url, tmp_in)
                    out_file = out_path / f"{_sanitize_base(Path(name).stem)}.py"
                    _ensure_dir(out_file)
                    _run_codegen(str(tmp_in), str(out_file))
                except Exception as e:
                    failures.append(name)
                    typer.secho(f"Failed: {name} -> {e}", fg="red")
            if failures:
                typer.secho(f"Completed with failures: {len(failures)}", fg="yellow")
                raise typer.Exit(code=1)
        return

    # local path
    in_path = Path(input)
    if not in_path.exists():
        raise typer.BadParameter(f"Input not found: {in_path}")
    inputs = _local_inputs(in_path)
    if not inputs:
        raise typer.BadParameter("No OpenAPI files found")
    if len(inputs) == 1 and out_path.suffix == ".py":
        _ensure_dir(out_path)
        _run_codegen(str(inputs[0]), str(out_path))
        return
    if out_path.suffix == ".py":
        raise typer.BadParameter("Output must be a directory when processing multiple files")
    out_path.mkdir(parents=True, exist_ok=True)
    failures: List[str] = []
    for p in inputs:
        try:
            out_file = out_path / f"{_sanitize_base(p.stem)}.py"
            _ensure_dir(out_file)
            _run_codegen(str(p), str(out_file))
        except Exception as e:
            failures.append(str(p))
            typer.secho(f"Failed: {p} -> {e}", fg="red")
    if failures:
        typer.secho(f"Completed with failures: {len(failures)}", fg="yellow")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()


