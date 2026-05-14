import os
from huggingface_hub import hf_hub_download, snapshot_download

MODELS_DIR = os.getenv("MODELS_DIR", "/app/models")
GEMMA_REPO = os.getenv("GEMMA_REPO", "litert-community/gemma-4-E2B-it-litert-lm")
GEMMA_FILE = os.getenv("GEMMA_FILE", "gemma-4-E2B-it.litertlm")
EMBED_REPO = os.getenv("EMBEDDING_REPO", "sentence-transformers/all-MiniLM-L6-v2")


def main() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)

    gemma_target = os.path.join(MODELS_DIR, GEMMA_FILE)
    if not os.path.exists(gemma_target):
        print(f"Downloading {GEMMA_FILE} from {GEMMA_REPO}...")
        hf_hub_download(
            repo_id=GEMMA_REPO,
            filename=GEMMA_FILE,
            local_dir=MODELS_DIR,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
    else:
        print(f"Found existing {gemma_target}, skipping.")

    embed_dir = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")
    if not os.path.exists(embed_dir):
        print(f"Downloading embedding model from {EMBED_REPO}...")
        snapshot_download(
            repo_id=EMBED_REPO,
            local_dir=embed_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
    else:
        print(f"Found existing {embed_dir}, skipping.")


if __name__ == "__main__":
    main()
