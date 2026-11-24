#!/usr/bin/env python3
import os
from config import load_config

config = load_config()
os.environ.update({
    "OLLAMA_HOST": "127.0.0.1:11434",
    "OLLAMA_NO_CLOUD": "1",
    "OLLAMA_MODELS": "/workspace/models",
    "OLLAMA_CONTEXT_LENGTH": str(config["context_length"]),
    "OLLAMA_NUM_PARALLEL": "1",
    "OLLAMA_MAX_LOADED_MODELS": "1",
    "OLLAMA_MAX_QUEUE": "4",
    "OLLAMA_KEEP_ALIVE": "30m",
    "OLLAMA_FLASH_ATTENTION": "1",
    "OLLAMA_KV_CACHE_TYPE": "q8_0",
})
os.execvp("ollama", ["ollama", "serve"])
