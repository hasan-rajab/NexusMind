"""Service startup must not depend on a writable Kaggle filesystem."""
import importlib.util
import json
from pathlib import Path


def load_logger():
    path=Path(__file__).resolve().parents[1]/'logger.py'
    spec=importlib.util.spec_from_file_location('nexus_logger_paths_test',path)
    logger=importlib.util.module_from_spec(spec);spec.loader.exec_module(logger)
    return logger,path


def test_default_logs_are_under_repo_data_directory(monkeypatch):
    monkeypatch.delenv('NEXUSMIND_LOG_DIR',raising=False)
    logger,path=load_logger()
    assert Path(logger.LOG_DIR)==path.parent/'data'/'logs'


def test_explicit_log_directory_is_used_for_interaction_writes(tmp_path,monkeypatch):
    monkeypatch.setenv('NEXUSMIND_LOG_DIR',str(tmp_path/'logs'))
    logger,_=load_logger()
    logger.log_interaction('test-turn','assistant','test question','test response',[])
    path=tmp_path/'logs'/'interactions.jsonl'
    assert json.loads(path.read_text())['turn_id']=='test-turn'
