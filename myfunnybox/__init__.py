import os

SRC_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.join(SRC_DIR, '..')
MODELS_DIR = os.path.join(PROJECT_DIR, 'models')
TESTS_DIR = os.path.join(PROJECT_DIR, "tests")
TESTS_DATA_DIR = os.path.join(TESTS_DIR, "data")