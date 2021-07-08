from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "AutoInvent Schema"
copyright = "2021 AutoInvent"
author = "AutoInvent"
release, version = get_version("autoinvent-schema")

# General --------------------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "pallets_sphinx_themes",
    "sphinxcontrib.log_cabinet",
    "sphinx_issues",
]
autoclass_content = "both"
autodoc_class_signature = "separated"
autodoc_default_options = {"members": True}
autodoc_member_order = "bysource"
# autodoc_preserve_defaults = True
autodoc_typehints = "description"
intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}
issues_github_path = "autoinvent/autoinvent-schema-py"

# HTML -----------------------------------------------------------------

html_theme = "flask"
html_context = {
    "project_links": [
        ProjectLink("PyPI Releases", "https://pypi.org/project/autoinvent-schema/"),
        ProjectLink(
            "Source Code", "https://github.com/autoinvent/autoinvent-schema-py/"
        ),
        ProjectLink(
            "Issue Tracker",
            "https://github.com/autoinvent/autoinvent-schema-py/issues/",
        ),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_title = f"{project} Documentation ({version})"
html_show_sourcelink = False
