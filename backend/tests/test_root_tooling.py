import os
import re
import json

def test_directories_exist():
    """Verify that the core monorepo directories exist."""
    required_dirs = ["frontend", "backend", "workers", "shared"]
    for d in required_dirs:
        assert os.path.isdir(d), f"Directory '{d}' does not exist"

def test_env_example_secrets():
    """Verify .env.example exists and contains no hardcoded secrets."""
    env_path = ".env.example"
    assert os.path.isfile(env_path), ".env.example does not exist"
    
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check for AWS keys, Stripe keys, JWT, Private Keys, or obvious secret assignments
    # AWS Keys pattern: AKIA...
    assert not re.search(r"AKIA[A-Z0-9]{16}", content), "Found hardcoded AWS Access Key in .env.example"
    
    # Check for secret values that don't look like instructions or placeholders
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            val = val.strip()
            # If the value has something like a real API key or password
            if val and not any(p in val.lower() for p in ["change", "placeholder", "your_", "true", "false", "http", "valkey", "postgres", "minioadmin", "info", "development", "3600", "30000", "3", "1280", "720", "6379", "5432", "8000"]):
                # Make sure it's not a secret looking string
                if len(val) > 16 and re.match(r"^[a-zA-Z0-9_\-\+]{16,}$", val):
                    assert False, f"Potential hardcoded secret found in .env.example for key {key}: '{val}'"

def test_docker_compose_exists_and_valid():
    """Verify docker-compose.yml exists and has basic structure."""
    compose_path = "docker-compose.yml"
    assert os.path.isfile(compose_path), "docker-compose.yml does not exist"
    
    # Simple check for docker-compose keys
    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "services:" in content, "docker-compose.yml does not contain 'services:' root key"
    assert "postgres:" in content, "docker-compose.yml missing 'postgres' service"
    assert "valkey:" in content, "docker-compose.yml missing 'valkey' service"
    assert "minio:" in content, "docker-compose.yml missing 'minio' service"

def test_lint_and_formatting_configs():
    """Verify eslint, prettier, tsconfig, and pyproject.toml are present."""
    required_files = [
        "tsconfig.json",
        "pyproject.toml",
        ".eslintrc.json",
        ".prettierrc"
    ]
    for file in required_files:
        assert os.path.isfile(file), f"Configuration file '{file}' is missing"

def test_tsconfig_parses():
    """Verify tsconfig.json is valid JSON."""
    assert os.path.isfile("tsconfig.json")
    with open("tsconfig.json", "r", encoding="utf-8") as f:
        # Strip comments if any (simple JSON parsing)
        lines = []
        for line in f:
            if not line.strip().startswith("//"):
                lines.append(line)
        try:
            config = json.loads("".join(lines))
            assert "compilerOptions" in config, "tsconfig.json is missing compilerOptions"
        except Exception as e:
            assert False, f"Failed to parse tsconfig.json: {e}"
