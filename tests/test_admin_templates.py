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
        admin_config={
            "prefix": "admin",
            "templates": "admin",
            "brand_name": "Test CMS",
            "title": "Test CMS Admin",
            "home_label": "Website",
            "home_url": "/",
        },
    )
    app.include_router(router)
    return TestClient(app)


PREFIX = "admin"


class TestAdminEditorTemplate:
    def test_editor_javascript_is_in_its_own_template(self):
        templates = Path(__file__).parent.parent / "src" / "moosey_cms" / "_admin_templates"
        editor_html = (templates / "editor.html").read_text()
        editor_js = (templates / "editor.js").read_text()

        assert 'src="/__moosey/static/admin/editor.js"' in editor_html
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
        assert "editor.min.css" in resp.text
        assert "editor-all.min.js" in resp.text

    def test_editor_uses_horizontal_preview_and_all_plugins(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        # JavaScript is now loaded as external file, check for script tag
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text
        # Check that editor.js is loaded after TUI dependencies
        assert resp.text.index("editor.min.css") < resp.text.index("editor.js")

    def test_editor_has_runtime_preview_style_toggle(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert 'id="preview-style-toggle"' in resp.text
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text

    def test_guifier_deletions_offer_undo_growl(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text
        # Check for Guifier import
        assert "Guifier" in resp.text

    def test_editor_has_supported_frontmatter_picker(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        assert 'id="metadata-field-toggle"' in resp.text
        assert 'id="metadata-field-search"' in resp.text
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text

    def test_editor_loads_plugin_dependencies_before_plugins(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        html = resp.text
        assert html.index("/__moosey/static/vendor/toast-ui/chart.min.js") < html.index(
            "/__moosey/static/vendor/toast-ui/plugins/chart.min.js"
        )
        assert html.index("/__moosey/static/vendor/toast-ui/color-picker.min.js") < html.index(
            "/__moosey/static/vendor/toast-ui/plugins/color-syntax.min.js"
        )
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in html

    def test_editor_has_indent_and_outdent_buttons(self, client):
        resp = client.get(f"/{PREFIX}/edit/")
        assert resp.status_code == 200
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text
        
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
        # JavaScript is now loaded as external file
        assert 'src="/__moosey/static/admin/editor.js"' in resp.text


class TestAdminLayout:
    def test_layout_has_responsive_sidebar_and_home_link(self, client):
        resp = client.get(f"/{PREFIX}/")
        assert resp.status_code == 200
        assert 'id="sidebar-toggle"' in resp.text
        assert 'aria-controls="sidebar"' in resp.text
        assert 'id="sidebar-overlay"' in resp.text
        assert 'data-sidebar-label' in resp.text
        assert 'href="/"' in resp.text
        assert "Test CMS Admin" in resp.text
        assert "Test CMS" in resp.text
        assert ">Website</span>" in resp.text
        assert 'data-admin-brand="Test CMS"' in resp.text

    def test_sidebar_script_supports_persistent_desktop_collapse(self):
        project_root = Path(__file__).parent.parent
        static_js = (
            project_root / "src" / "moosey_cms" / "_static" / "admin" / "admin.js"
        ).read_text()
        template_js = (
            project_root / "src" / "moosey_cms" / "_admin_templates" / "admin.js"
        ).read_text()

        assert static_js == template_js
        assert "moosey-admin-sidebar-collapsed" in static_js
        assert "sidebarBreakpoint.matches" in static_js
        assert "'md:w-20'" in static_js
        assert "setMobileSidebarOpen" in static_js


class TestAdminDashboardTemplate:
    def test_dashboard_renders(self, client):
        """Test that dashboard template renders."""
        resp = client.get(f"/{PREFIX}/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text or "dashboard" in resp.text.lower()
        assert 'id="content-stat-files"' in resp.text
        assert 'id="uploads-stat-files"' in resp.text
        assert "Uploaded Files" in resp.text
        assert "fetch('/' + prefix + '/stats')" in resp.text

    def test_dashboard_spacing_utility_is_built(self):
        """Tailwind must scan the admin sources and generate dashboard spacing."""
        project_root = Path(__file__).parent.parent
        input_css = (project_root / "src" / "moosey_cms" / "_styles" / "admin.css").read_text()
        admin_css = (
            project_root / "src" / "moosey_cms" / "_static" / "admin" / "admin.css"
        ).read_text()
        package_json = (project_root / "package.json").read_text()

        assert '@source "../_admin_templates"' in input_css
        assert '"build:admin-css"' in package_json
        assert "/*! tailwindcss" in admin_css
        assert ".space-y-8" in admin_css


class TestAdminListTemplate:
    def test_list_renders(self, client):
        """Test that list template renders."""
        resp = client.get(f"/{PREFIX}/browse/")
        assert resp.status_code == 200
        assert "index.md" in resp.text or "browse" in resp.text.lower()
        assert 'id="new-file-directory"' in resp.text
        assert 'for="new-file-name"' in resp.text
        assert 'aria-label="Markdown file name"' in resp.text
        assert ">.md</span" in resp.text
        assert 'id="new-dir-directory"' in resp.text
        assert 'for="new-dir-name"' in resp.text
        assert 'aria-label="Folder name"' in resp.text
        assert 'id="content-list"' in resp.text
        assert 'class="fuzzy-search' in resp.text
        assert 'id="content-sort"' in resp.text
        assert (
            '<option value="entry-modified:desc" selected>'
            "Modified: newest first</option>"
        ) in resp.text
        assert resp.text.index("vendor/list.js/list.min.js") < resp.text.index(
            'static/admin/list.js'
        )
        assert 'id="content-page-size"' in resp.text
        assert '<option value="20" selected>20</option>' in resp.text
        assert '<option value="50">50</option>' in resp.text
        assert '<option value="100">100</option>' in resp.text
        assert 'class="pagination"' in resp.text

        nested = client.get(f"/{PREFIX}/browse/blog")
        assert nested.status_code == 200
        assert 'subpath: "blog"' in nested.text
