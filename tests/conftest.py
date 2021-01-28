def pytest_addoption(parser):
    parser.addoption("--optionals", action="store_true", help="include optional tests")
