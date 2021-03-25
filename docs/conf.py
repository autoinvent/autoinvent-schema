from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "Conveyor Schema"
copyright = "2021 David Lord"
author = "David Lord"
release, version = get_version("conveyor-schema")

# General --------------------------------------------------------------

master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "pallets_sphinx_themes",
    "sphinxcontrib.log_cabinet",
    "sphinx_issues",
]
intersphinx_mapping = {"python": ("https://docs.python.org/3/", None)}
issues_github_path = "autoinvent/py-conveyor-schema"

# HTML -----------------------------------------------------------------

html_theme = "flask"
html_context = {
    "project_links": [
        ProjectLink("PyPI Releases", "https://pypi.org/project/conveyor-schema/"),
        ProjectLink("Source Code", "https://github.com/autoinvent/py-conveyor-schema/"),
        ProjectLink(
            "Issue Tracker", "https://github.com/autoinvent/py-conveyor-schema/issues/"
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
