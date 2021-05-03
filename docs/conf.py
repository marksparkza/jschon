project = 'jschon'
author = 'Mark Jacobson'
copyright = '2021, Mark Jacobson'
release = '0.2.0'

extensions = ['sphinx.ext.autodoc']
templates_path = ['_templates']
exclude_patterns = ['_build']
html_theme = 'classic'
html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'member-order': 'groupwise',
    'undoc-members': True,
}
