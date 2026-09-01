# きのこクイズ

## PCでの きどう

このプロジェクトでは、Python 3.10いじょうをつかう。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

がめんにでた `http://127.0.0.1:7860` をブラウザでひらく。

## てすと

```bash
.venv/bin/python -m pytest -q
```

## Google Colabでの きどう

[Colab用ノートブック](colab/launch_kinoko_quiz.ipynb)をひらき、さいしょのセルにGitHubリポジトリのURLをいれてから、上からじゅんに実行する。

4〜5歳の子どもを対象にした、PC向けのきのこ教育ゲームです。

現在はGitHubベースでゼロから再構築しています。確定仕様は `docs/SPEC.md` を参照してください。
