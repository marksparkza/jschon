project = 'jschon'
author = 'Mark Jacobson'
copyright = '2021, Mark Jacobson'
release = '0.2.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
]
exclude_patterns = ['_build']

autodoc_default_options = {
    'members': True,
    'member-order': 'groupwise',
    'undoc-members': True,
}

html_theme = 'sphinx_rtd_theme'
