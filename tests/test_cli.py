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


    def test_list_exclude_folder(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
            "--exclude-folder", "Tech",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        # "Nested Article" is in Tech folder, should be excluded
        urls = [b["url"] for b in data]
        assert "https://example.com/nested" not in urls
        assert "https://example.com/article" in urls

    def test_list_include_folder(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
            "--include-folder", "Tech",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Only "Nested Article" is in Tech folder
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com/nested"

    def test_list_exclude_and_include_combined(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = str(tmp_home / ".bookmark2skill" / "manifest.json")
        # Include Bookmarks bar (both items), then exclude Tech (removes nested)
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
            "--include-folder", "Bookmarks bar",
            "--exclude-folder", "Tech",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        urls = [b["url"] for b in data]
        assert "https://example.com/article" in urls
        assert "https://example.com/nested" not in urls


class TestFetchCommand:
    def test_fetch_outputs_markdown(self, runner, httpx_mock):
        httpx_mock.add_response(
            url="https://example.com/article",
            html="<html><body><article><h1>Title</h1><p>Content here.</p></article></body></html>",
        )
        result = runner.invoke(cli, ["fetch", "--renderer", "direct", "https://example.com/article"])
        assert result.exit_code == 0
        assert "Content here" in result.output

    def test_fetch_error_shows_message(self, runner, httpx_mock):
        httpx_mock.add_response(url="https://example.com/missing", status_code=404)
        result = runner.invoke(cli, ["fetch", "--renderer", "direct", "https://example.com/missing"])
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


class TestSearchCommand:
    def test_search_finds_matching_skill(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        result = runner.invoke(cli, [
            "search", "simplicity", "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) >= 1
        assert data[0]["score"] > 0
        assert "engineering/system-design" in data[0]["category"]

    def test_search_no_results(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        result = runner.invoke(cli, [
            "search", "quantum-physics-xyz", "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 0

    def test_search_ranks_by_relevance(self, runner, tmp_path, sample_distilled_data):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        # Write skill with "system-design" in tags
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        result = runner.invoke(cli, [
            "search", "system-design", "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) >= 1
        # Should match on tags (weight 3) at minimum
        assert data[0]["score"] >= 3


class TestManifestBackup:
    def test_manifest_creates_backup_on_save(self, runner, chrome_bookmarks_file, tmp_home):
        manifest_path = tmp_home / ".bookmark2skill" / "manifest.json"
        bak_path = tmp_home / ".bookmark2skill" / "manifest.json.bak"
        runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", str(manifest_path),
        ])
        # First save creates manifest but no .bak (no pre-existing file to back up from _load)
        # Second operation should create .bak
        runner.invoke(cli, [
            "mark-done", "https://example.com/article",
            "--manifest-path", str(manifest_path),
        ])
        assert bak_path.is_file()
        # .bak should be valid JSON
        bak_data = json.loads(bak_path.read_text())
        assert "bookmarks" in bak_data


class TestEndToEnd:
    def test_full_workflow(self, runner, tmp_path, chrome_bookmarks_file, sample_distilled_data, httpx_mock):
        """Test the complete workflow: list → fetch → write-obsidian → write-skill → mark-done → status."""
        vault = tmp_path / "vault"
        vault.mkdir()
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        manifest_path = str(tmp_path / "manifest.json")

        # Step 1: list
        result = runner.invoke(cli, [
            "list", "--source", str(chrome_bookmarks_file),
            "--manifest-path", manifest_path,
        ])
        assert result.exit_code == 0
        bookmarks = json.loads(result.output)
        assert len(bookmarks) == 2

        # Step 2: fetch
        httpx_mock.add_response(
            url="https://example.com/article",
            html="<html><body><article><h1>Test</h1><p>Great content.</p></article></body></html>",
        )
        result = runner.invoke(cli, ["fetch", "--renderer", "direct", "https://example.com/article"])
        assert result.exit_code == 0

        # Step 3: write-obsidian
        data_file = tmp_path / "distilled.json"
        data_file.write_text(json.dumps(sample_distilled_data), encoding="utf-8")
        result = runner.invoke(cli, [
            "write-obsidian",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--vault-path", str(vault),
        ])
        assert result.exit_code == 0
        obsidian_path = json.loads(result.output)["path"]

        # Step 4: write-skill
        result = runner.invoke(cli, [
            "write-skill",
            "--url", "https://example.com/article",
            "--data", str(data_file),
            "--category", "engineering/system-design",
            "--skill-dir", str(skill_dir),
        ])
        assert result.exit_code == 0
        skill_path = json.loads(result.output)["path"]

        # Step 5: mark-done
        result = runner.invoke(cli, [
            "mark-done", "https://example.com/article",
            "--manifest-path", manifest_path,
            "--obsidian-path", obsidian_path,
            "--skill-path", skill_path,
        ])
        assert result.exit_code == 0

        # Step 6: status
        result = runner.invoke(cli, ["status", "--manifest-path", manifest_path])
        assert result.exit_code == 0
        status = json.loads(result.output)
        assert status["done"] == 1
        assert status["pending"] == 1
        assert status["total"] == 2
