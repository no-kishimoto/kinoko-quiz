"""Drive移行とColabの作業コピー。Driveの原本は起動時に変更しない。"""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import uuid

EXCLUDED = {'.git', '.venv', '__pycache__', '.pytest_cache', '.godot'}
REQUIRED = ('app.py', 'requirements.txt', 'src/ui.py', 'data/kinoko.json',
            'data/shokubutsu.json', 'data/konchuu.json', 'data/kyouryuu.json',
            'colab/launch_kinoko_quiz.ipynb')


def project_files(root):
    root = Path(root)
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f'リンクファイルは移行できません: {relative}')
        if path.is_file():
            yield path, relative


def validate_project(root):
    root = Path(root)
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if not (root / 'assets/images').is_dir():
        missing.append('assets/images/')
    if missing:
        raise FileNotFoundError('ゲームのファイルが不足しています: ' + ', '.join(missing))


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def copy_project(source, destination):
    files = list(project_files(source))
    manifest = {}
    for index, (path, relative) in enumerate(files, 1):
        target = Path(destination) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = digest(path)
        shutil.copyfile(path, target)
        if digest(target) != expected:
            raise IOError(f'コピーの検証に失敗しました: {relative}')
        manifest[relative.as_posix()] = expected
        if index % 25 == 0 or index == len(files):
            print(f'コピー・照合: {index}/{len(files)} ファイル', flush=True)
    return manifest


def migrate_project(source, destination, origin):
    """新規フォルダのみ作成。全ファイル照合後に正式名にする。"""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    validate_project(source)
    if destination.exists():
        raise FileExistsError(f'既存フォルダは上書きしません: {destination}')
    if destination == source or source in destination.parents:
        raise ValueError('移行先は元のプロジェクトの外に指定してください。')
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + '.移行中-' + uuid.uuid4().hex[:8])
    partial.mkdir()
    try:
        manifest = copy_project(source, partial)
        (partial / 'DRIVE_MIGRATION.json').write_text(json.dumps(
            {'origin': origin, 'files': manifest}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        validate_project(partial)
        if destination.exists():
            raise FileExistsError(f'移行先が作成されています: {destination}')
        partial.rename(destination)
    except BaseException:
        # 中断時も、もともと存在したフォルダには触れない。
        shutil.rmtree(partial, ignore_errors=True)
        raise
    print(f'移行完了: {destination}（{len(manifest)}ファイルを照合済み）', flush=True)
    return manifest


def prepare_local_project(source, workspace):
    """毎回Driveの現在の内容から作業コピーを作り、古い版を使わない。"""
    validate_project(source)
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix='kinoko-quiz-', dir=workspace))
    try:
        copy_project(source, destination)
        validate_project(destination)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination
