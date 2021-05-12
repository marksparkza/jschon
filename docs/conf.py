import jschon

project = 'jschon'
author = 'Mark Jacobson'
copyright = '2021, Mark Jacobson'
release = jschon.__version__

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
]
exclude_patterns = ['_build']

autodoc_default_options = {
    'members': True,
    'member-order': 'groupwise',
    'special-members': '__init__, __new__, __call__',
    'undoc-members': True,
}
autodoc_typehints = 'description'
autodoc_inherit_docstrings = False

html_theme = 'sphinx_rtd_theme'
