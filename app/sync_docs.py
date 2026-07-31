import shutil
import subprocess
from pathlib import Path

import httpx

from app.config import settings

REPO_URL = "https://github.com/kubernetes/website.git"

SECTIONS = [
    "content/en/docs/concepts",
    "content/en/docs/tasks",
    "content/en/docs/tutorials",
    "content/en/docs/setup",
    "content/en/docs/reference/kubectl",
    "content/en/docs/reference/access-authn-authz",
    "content/en/docs/reference/networking",
]


def sync_kubernetes_docs() -> Path:
    clone_dir = Path("/tmp/k8s-website")
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO_URL, str(clone_dir)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(clone_dir), "sparse-checkout", "set", *SECTIONS],
        check=True,
    )

    dest = Path(settings.docs_path) / "kubernetes.io"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    for section in SECTIONS:
        src = clone_dir / section
        if src.exists():
            shutil.copytree(src, dest / Path(section).name, dirs_exist_ok=True)

    shutil.rmtree(clone_dir)
    return dest


def trigger_ingest() -> None:
    response = httpx.post("http://rag-app:8000/ingest", timeout=600)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    dest = sync_kubernetes_docs()
    print(f"Synced kubernetes.io docs into {dest}")
    trigger_ingest()
