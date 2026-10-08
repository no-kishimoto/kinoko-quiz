"""移行が原本を保護し、Drive上の編集を次回起動に反映することを確認。"""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('drive_files', Path(__file__).parents[1] / 'colab/drive_files.py')
drive_files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive_files)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'source'
    for name in drive_files.REQUIRED:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('original')
    image = root / 'assets/images/insect.png'
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b'\x00\xffimage')
    (root / '.git').mkdir()
    (root / '.git/config').write_text('excluded')
    return root


def test_migration_copies_and_records_all_original_files(source, tmp_path):
    destination = tmp_path / 'drive/game'
    manifest = drive_files.migrate_project(source, destination, 'test archive')
    assert not (destination / '.git').exists()
    assert (destination / 'assets/images/insect.png').read_bytes() == b'\x00\xffimage'
    assert manifest == json.loads((destination / 'DRIVE_MIGRATION.json').read_text())['files']
    for relative, checksum in manifest.items():
        assert drive_files.digest(destination / relative) == checksum


def test_existing_drive_files_are_never_overwritten(source, tmp_path):
    destination = tmp_path / 'drive/game'
    destination.mkdir(parents=True)
    marker = destination / 'important.txt'
    marker.write_text('family data')
    with pytest.raises(FileExistsError):
        drive_files.migrate_project(source, destination, 'test')
    assert marker.read_text() == 'family data'
    assert list(destination.iterdir()) == [marker]


def test_corrupted_copy_does_not_publish_partial_project(source, tmp_path, monkeypatch):
    destination = tmp_path / 'drive/game'
    def corrupted_copy(original, target):
        Path(target).write_bytes(b'corrupted')
    monkeypatch.setattr(drive_files.shutil, 'copyfile', corrupted_copy)
    with pytest.raises(IOError, match='コピーの検証'):
        drive_files.migrate_project(source, destination, 'test')
    assert not destination.exists()
    assert not list(destination.parent.glob('game.移行中-*'))
    assert (source / 'app.py').read_text() == 'original'


def test_next_launch_reads_drive_edits_and_keeps_original_unchanged(source, tmp_path):
    first = drive_files.prepare_local_project(source, tmp_path / 'runtime')
    (first / 'app.py').write_text('temporary edit')
    assert (source / 'app.py').read_text() == 'original'
    (source / 'app.py').write_text('drive edit')
    second = drive_files.prepare_local_project(source, tmp_path / 'runtime')
    assert second != first
    assert (second / 'app.py').read_text() == 'drive edit'


def test_launcher_has_no_github_dependency_and_requires_setup():
    notebook = json.loads((Path(__file__).parents[1] / 'colab/launch_kinoko_quiz.ipynb').read_text())
    code = [''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code']
    for cell in code:
        compile(cell, '<colab>', 'exec')
        assert 'github' not in cell.lower()
    with pytest.raises(RuntimeError, match='準備完了'):
        exec(code[-1], {})
