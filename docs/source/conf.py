project = "geometry-to-spatialite"
copyright = "2020, Chris Shaw"
author = "Chris Shaw"
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]
master_doc = "index"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_favicon = "data:image/svg+xml,&#60;svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22&#62;&#60;text y=%22.9em%22 font-size=%2290%22&#62;🌍&#60;/text&#62;&#60;/svg&#62;"
autoclass_content = "both"
