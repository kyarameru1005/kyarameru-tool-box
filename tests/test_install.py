from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("installer", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_source_tree(root: Path) -> None:
    (root / "toolbox" / "skills" / "plan-worker").mkdir(parents=True)
    (root / "toolbox" / "skills" / "mcp-worker").mkdir(parents=True)
    (root / "toolbox" / "hooks").mkdir(parents=True)
    (root / "toolbox" / "prompts").mkdir(parents=True)

    (root / "toolbox" / "skills" / "plan-worker" / "SKILL.md").write_text("plan", encoding="utf-8")
    (root / "toolbox" / "skills" / "mcp-worker" / "SKILL.md").write_text("mcp", encoding="utf-8")
    (root / "toolbox" / "hooks" / "preflight.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (root / "toolbox" / "AGENTS.md").write_text("# global agents\n", encoding="utf-8")


def test_iter_source_entries_maps_to_codex_home(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)

    fake_home = tmp_path / "home"
    entries = installer.iter_source_entries(root=tmp_path, home=fake_home)

    targets = {e.target for e in entries}
    assert fake_home / ".codex" / "skills" / "plan-worker" in targets
    assert fake_home / ".codex" / "skills" / "mcp-worker" in targets
    assert fake_home / ".codex" / "hooks" / "preflight.sh" in targets
    assert fake_home / ".codex" / "AGENTS.md" in targets


def test_install_copy_and_manifest(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"

    rc = installer.install(mode="copy", dry_run=False, root=tmp_path, home=fake_home)
    assert rc == 0

    plan_skill = fake_home / ".codex" / "skills" / "plan-worker" / "SKILL.md"
    assert plan_skill.exists()
    assert plan_skill.read_text(encoding="utf-8") == "plan"
    global_agents = fake_home / ".codex" / "AGENTS.md"
    assert global_agents.exists()
    assert global_agents.read_text(encoding="utf-8") == "# global agents\n"

    manifest = fake_home / ".codex" / installer.MANIFEST_FILENAME
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["app"] == installer.APP_NAME
    assert str(fake_home / ".codex" / "skills" / "plan-worker") in data["paths"]
    assert str(fake_home / ".codex" / "AGENTS.md") in data["paths"]


def test_unmanaged_target_is_not_overwritten(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"

    unmanaged = fake_home / ".codex" / "hooks" / "preflight.sh"
    unmanaged.parent.mkdir(parents=True, exist_ok=True)
    unmanaged.write_text("custom", encoding="utf-8")

    installer.install(mode="copy", dry_run=False, root=tmp_path, home=fake_home)
    assert unmanaged.read_text(encoding="utf-8") == "custom"


def test_existing_agents_is_backed_up_and_replaced_on_copy(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"
    existing_agents = fake_home / ".codex" / "AGENTS.md"
    existing_agents.parent.mkdir(parents=True, exist_ok=True)
    existing_agents.write_text("# custom agents\n", encoding="utf-8")

    installer.install(mode="copy", dry_run=False, root=tmp_path, home=fake_home)

    assert existing_agents.read_text(encoding="utf-8") == "# global agents\n"
    backups = sorted((fake_home / ".codex").glob("AGENTS.md.bak.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "# custom agents\n"


def test_existing_agents_is_backed_up_and_replaced_on_link(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"
    existing_agents = fake_home / ".codex" / "AGENTS.md"
    existing_agents.parent.mkdir(parents=True, exist_ok=True)
    existing_agents.write_text("# custom agents\n", encoding="utf-8")

    installer.install(mode="link", dry_run=False, root=tmp_path, home=fake_home)

    assert existing_agents.is_symlink()
    assert existing_agents.resolve() == (tmp_path / "toolbox" / "AGENTS.md").resolve()
    backups = sorted((fake_home / ".codex").glob("AGENTS.md.bak.*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "# custom agents\n"


def test_dry_run_keeps_filesystem_clean(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"

    installer.install(mode="copy", dry_run=True, root=tmp_path, home=fake_home)

    assert not (fake_home / ".codex" / "skills" / "plan-worker").exists()
    assert not (fake_home / ".codex" / installer.MANIFEST_FILENAME).exists()
    assert not (fake_home / ".codex" / "AGENTS.md").exists()
    assert not list((fake_home / ".codex").glob("AGENTS.md.bak.*"))


def test_uninstall_removes_only_managed(tmp_path: Path):
    installer = load_module()
    create_source_tree(tmp_path)
    fake_home = tmp_path / "home"

    installer.install(mode="copy", dry_run=False, root=tmp_path, home=fake_home)

    keep_file = fake_home / ".codex" / "hooks" / "keep.sh"
    keep_file.parent.mkdir(parents=True, exist_ok=True)
    keep_file.write_text("keep", encoding="utf-8")
    agents_backup = fake_home / ".codex" / "AGENTS.md.bak.manual"
    agents_backup.write_text("# backup\n", encoding="utf-8")

    installer.uninstall(dry_run=False, home=fake_home)

    assert keep_file.exists()
    assert agents_backup.exists()
    assert not (fake_home / ".codex" / "skills" / "plan-worker").exists()
    assert not (fake_home / ".codex" / "AGENTS.md").exists()
    assert not (fake_home / ".codex" / installer.MANIFEST_FILENAME).exists()


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def setup_policy_repo(tmp_path: Path, workflow_content: str) -> None:
    policy_script = Path(__file__).resolve().parents[1] / "scripts" / "policy-check.sh"
    write_file(
        tmp_path / "AGENTS.md",
        "# AGENTS\n目的\n優先\n応答\n実行\nGit\nログ\n命名\nkebab-case\nPR本文を正本とする\n",
    )
    write_file(
        tmp_path / "toolbox" / "AGENTS.md",
        "# AGENTS\n目的\n優先\n応答\n実行\nGit\nログ\n命名\nkebab-case\nPR本文を正本とする\n",
    )
    write_file(
        tmp_path / ".github" / "workflows" / "tests.yml",
        workflow_content,
    )
    write_file(
        tmp_path / "toolbox" / "skills" / "agents-md-writer" / "scripts" / "check_agents_md.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\necho \"[OK] mock check: $1\"\n",
    )
    write_file(
        tmp_path / "docs" / "pr-template.md",
        "## 目的\n- test\n\n## 主な変更点\n- test\n\n## 検証結果\n- test\n",
    )
    write_file(
        tmp_path / "scripts" / "create-pr.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\necho \"mock\"\n",
    )
    write_file(tmp_path / "scripts" / "policy-check.sh", policy_script.read_text(encoding="utf-8"))
    subprocess.run(["chmod", "+x", str(tmp_path / "scripts" / "create-pr.sh")], check=True)
    subprocess.run(["chmod", "+x", str(tmp_path / "scripts" / "policy-check.sh")], check=True)
    subprocess.run(
        ["chmod", "+x", str(tmp_path / "toolbox" / "skills" / "agents-md-writer" / "scripts" / "check_agents_md.sh")],
        check=True,
    )


def test_policy_check_passes_with_required_files_and_workflow(tmp_path: Path):
    setup_policy_repo(
        tmp_path,
        "name: tests\non:\n  push:\n  pull_request:\njobs:\n  tests:\n    runs-on: ubuntu-latest\n  harness:\n    runs-on: ubuntu-latest\n    steps:\n      - run: bash scripts/harness.sh\n  agents-policy:\n    runs-on: ubuntu-latest\n",
    )

    result = subprocess.run(
        ["bash", "scripts/policy-check.sh"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[DONE] policy checks passed" in result.stdout


def test_policy_check_fails_when_workflow_is_missing(tmp_path: Path):
    setup_policy_repo(
        tmp_path,
        "name: tests\non:\n  push:\n  pull_request:\njobs:\n  tests:\n    runs-on: ubuntu-latest\n  harness:\n    runs-on: ubuntu-latest\n    steps:\n      - run: bash scripts/harness.sh\n  agents-policy:\n    runs-on: ubuntu-latest\n",
    )
    (tmp_path / ".github" / "workflows" / "tests.yml").unlink()

    result = subprocess.run(
        ["bash", "scripts/policy-check.sh"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "[ERROR] missing file: .github/workflows/tests.yml" in result.stdout


def test_policy_check_fails_when_harness_job_is_missing(tmp_path: Path):
    setup_policy_repo(
        tmp_path,
        "name: tests\non:\n  push:\n  pull_request:\njobs:\n  tests:\n    runs-on: ubuntu-latest\n  agents-policy:\n    runs-on: ubuntu-latest\n",
    )

    result = subprocess.run(
        ["bash", "scripts/policy-check.sh"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "workflow has harness job" in result.stdout


def test_policy_check_fails_when_pr_template_lacks_required_section(tmp_path: Path):
    setup_policy_repo(
        tmp_path,
        "name: tests\non:\n  push:\n  pull_request:\njobs:\n  tests:\n    runs-on: ubuntu-latest\n  harness:\n    runs-on: ubuntu-latest\n    steps:\n      - run: bash scripts/harness.sh\n  agents-policy:\n    runs-on: ubuntu-latest\n",
    )
    write_file(
        tmp_path / "docs" / "pr-template.md",
        "## 目的\n- test\n\n## 主な変更点\n- test\n",
    )

    result = subprocess.run(
        ["bash", "scripts/policy-check.sh"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "pr template has 検証結果 section" in result.stdout
