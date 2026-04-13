# tests/test_cli.py
import json
import pytest
from click.testing import CliRunner
from bookmark2skill.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestListCommand:
    def test_list_from_chrome_json(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list",
            "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        urls = [b["url"] for b in data]
        assert "https://example.com/article" in urls
        assert "https://example.com/nested" in urls

    def test_list_from_html(self, runner, html_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list",
            "--source", str(html_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) >= 2

    def test_list_marks_new_as_pending_in_manifest(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list",
            "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        manifest_data = json.loads(open(manifest_path).read())
        for entry in manifest_data["bookmarks"].values():
            assert entry["status"] == "pending"

    def test_list_skips_existing_urls(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        # Run twice
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
            "--only-new",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 0  # All already in manifest


class TestFetchCommand:
    def test_fetch_outputs_markdown(self, runner, httpx_mock):
        httpx_mock.add_response(
            url="https://example.com/article",
            html="<html><body><article><h1>Title</h1><p>Content here.</p></article></body></html>",
        )
        result = runner.invoke(cli, ["fetch", "https://example.com/article"])
        assert result.exit_code == 0
        assert "Content here" in result.output

    def test_fetch_error_shows_message(self, runner, httpx_mock):
        httpx_mock.add_response(url="https://example.com/missing", status_code=404)
        result = runner.invoke(cli, ["fetch", "https://example.com/missing"])
        assert result.exit_code != 0
        assert "404" in result.output


class TestWriteObsidianCommand:
    def test_write_from_structured_json(self, runner, tmp_path, sample_distilled_data):
        vault = tmp_path / "vault"
        vault.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        md_files = list(vault.rglob("*.md"))
        assert len(md_files) == 1
        content = md_files[0].read_text()
        assert "Simplicity is the ultimate sophistication" in content

    def test_write_raw_mode(self, runner, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        raw_file = tmp_path / "raw.md"
        raw_file.write_text("# My Raw Note\n\nContent here.", encoding="utf-8")
        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/raw",
            "--raw", str(raw_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        md_files = list(vault.rglob("*.md"))
        assert len(md_files) == 1
        assert "My Raw Note" in md_files[0].read_text()

    def test_write_creates_subdirectory_from_folder(self, runner, tmp_path, sample_distilled_data):
        vault = tmp_path / "vault"
        vault.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
            "--folder", "tech/articles",
        ])
        assert result.exit_code == 0
        assert (vault / "bookmark2skill" / "tech" / "articles").is_dir()


class TestWriteSkillCommand:
    def test_write_from_structured_json(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        md_files = list(skill_dir.rglob("*.md"))
        assert len(md_files) == 1
        assert "engineering/system-design" in str(md_files[0])

    def test_write_raw_mode(self, runner, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        raw_file = tmp_path / "raw.md"
        raw_file.write_text("---\nname: test\n---\nContent.", encoding="utf-8")
        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/raw",
            "--raw", str(raw_file),
            "--category", "thinking/mental-models",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        md_files = list(skill_dir.rglob("*.md"))
        assert len(md_files) == 1

    def test_category_creates_nested_dirs(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert (skill_dir / "engineering" / "system-design").is_dir()


class TestStatusCommand:
    def test_status_empty(self, runner, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total"] == 0

    def test_status_with_bookmarks(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["pending"] == 2
        assert data["total"] == 2


class TestMarkCommands:
    def test_mark_done(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--obsidian-path", "/vault/article.md",
            "--skill-path", "/skills/article.md",
        ])
        assert result.exit_code == 0
        status = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        data = json.loads(status.output)
        assert data["done"] == 1

    def test_mark_failed(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        result = runner.invoke(cli, [
            "mark-failed", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--reason", "HTTP 404",
        ])
        assert result.exit_code == 0
        status = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        data = json.loads(status.output)
        assert data["failed"] == 1

    def test_mark_unknown_url_fails(self, runner, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/unknown",
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code != 0
