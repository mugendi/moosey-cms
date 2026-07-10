"""
Tests for admin HTML templates (src/moosey_cms/_admin_templates/).

Verifies that templates render correctly with the new tabbed editor interface.
"""

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.testclient import TestClient
from pathlib import Path

from moosey_cms.admin import register_admin_routes


@pytest.fixture
def content_dir(tmp_path):
    """Create a content directory with sample markdown files."""
    d = tmp_path / "content"
    d.mkdir()
    (d / "index.md").write_text("---\ntitle: Home\n---\nBody content here.")
    return d


@pytest.fixture
def templates_dir(tmp_path):
    """Create a templates directory with admin templates."""
    d = tmp_path / "templates" / "admin"
    d.mkdir(parents=True)
    
    # Copy the actual templates
    templates_source = Path(__file__).parent.parent / "src" / "moosey_cms" / "_admin_templates"
    
    for template_file in templates_source.glob("*.html"):
        (d / template_file.name).write_text(template_file.read_text())

    # JavaScript files are Jinja templates included by the HTML templates.
    for template_file in templates_source.glob("*.js"):
        (d / template_file.name).write_text(template_file.read_text())
    
    return d


@pytest.fixture
def client(content_dir, templates_dir):
    """Create a TestClient with admin routes registered."""
    app = FastAPI()
    router = APIRouter()
    
    # Set up templates (matching how init_cms does it)
    templates = Jinja2Templates(
        env=Environment(
            loader=FileSystemLoader(str(templates_dir.parent)),
            autoescape=select_autoescape(["html"]),
            enable_async=True,
        ),
    )
    app.state.templates = templates
    
    register_admin_routes(
        router,
        dirs={"content": content_dir},
        mode="development",
        admin_config={"prefix": "admin", "templates": "admin"},
    )
    app.include_router(router)
    return TestClient(app)


PREFIX = "admin"


class TestAdminEditorTemplate:
    def test_editor_javascript_is_in_its_own_template(self):
        templates = Path(__file__).parent.parent / "src" / "moosey_cms" / "_admin_templates"
        editor_html = (templates / "editor.html").read_text()
        editor_js = (templates / "editor.js").read_text()

        assert '{% include admin_config.templates ~ "/editor.js" %}' in editor_html
        assert "function initTuiEditor()" not in editor_html
        assert "function initTuiEditor()" in editor_js

    def test_editor_renders_new_file(self, client):
        """Test that editor template renders for new files."""
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "New File" in resp.text
        assert "Content" in resp.text
        assert "Metadata" in resp.text
        
    def test_editor_renders_existing_file(self, client):
        """Test that editor template renders for existing files."""
        resp = client.get(f"/{PREFIX}/edit/index.md")
        assert resp.status_code == 200
        assert "<h1 class=\"text-2xl font-bold text-moose-900\">Edit</h1>" in resp.text
        assert "index.md" in resp.text
        assert "Content" in resp.text
        assert "Metadata" in resp.text
        
    def test_editor_has_tab_structure(self, client):
        """Test that editor has the tabbed interface structure."""
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "tab-content" in resp.text
        assert "tab-metadata" in resp.text
        assert "panel-content" in resp.text
        assert "panel-metadata" in resp.text
        
    def test_editor_loads_tui_editor(self, client):
        """Test that editor loads TUI Editor for markdown."""
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "toastui-editor" in resp.text
        assert "tui-editor" in resp.text

    def test_editor_uses_horizontal_preview_and_all_plugins(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "var previewStyle = 'vertical'" in resp.text
        assert "previewStyle: previewStyle" in resp.text
        for plugin in ("chart", "codeSyntaxHighlight", "colorSyntax", "tableMergedCell", "uml"):
            assert f"toastui.Editor.plugin.{plugin}" in resp.text

    def test_editor_has_runtime_preview_style_toggle(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert 'id="preview-style-toggle"' in resp.text
        assert "togglePreviewStyle()" in resp.text
        assert "tuiEditor.changePreviewStyle(previewStyle)" in resp.text
        assert "previewStyle === 'vertical' ? 'tab' : 'vertical'" in resp.text

    def test_guifier_deletions_offer_undo_growl(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "function checkGuifierForDeletion()" in resp.text
        assert "countDataNodes(current) < countDataNodes(guifierSnapshot)" in resp.text
        assert "A metadata item was removed" in resp.text
        assert "restoreGuifierSnapshot(previous)" in resp.text
        assert "moose-growl__action" in resp.text

    def test_editor_loads_plugin_dependencies_before_plugins(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        html = resp.text
        assert html.index("chart/latest/toastui-chart.min.js") < html.index(
            "editor-plugin-chart/latest/toastui-editor-plugin-chart.min.js"
        )
        assert html.index("tui-color-picker/latest/tui-color-picker.min.js") < html.index(
            "editor-plugin-color-syntax/latest/toastui-editor-plugin-color-syntax.min.js"
        )
        assert "plugins: availablePlugins" in html

    def test_editor_has_indent_and_outdent_buttons(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "Indent selected lines" in resp.text
        assert "Outdent selected lines" in resp.text
        
    def test_editor_loads_guifier(self, client):
        """Test that editor loads Guifier for YAML frontmatter."""
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "guifier" in resp.text.lower()
        
    def test_editor_has_save_button(self, client):
        """Test that editor has save button."""
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert "btn-save" in resp.text
        assert "Save" in resp.text
        assert 'id="save-spinner"' in resp.text
        assert "if (isSaving) return" in resp.text
        assert "setSaveState(true)" in resp.text
        assert "setSaveState(false)" in resp.text
        assert "button.disabled = saving" in resp.text


class TestAdminDashboardTemplate:
    def test_dashboard_renders(self, client):
        """Test that dashboard template renders."""
        resp = client.get(f"/{PREFIX}/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text or "dashboard" in resp.text.lower()


class TestAdminListTemplate:
    def test_list_renders(self, client):
        """Test that list template renders."""
        resp = client.get(f"/{PREFIX}/browse/")
        assert resp.status_code == 200
        assert "index.md" in resp.text or "browse" in resp.text.lower()
