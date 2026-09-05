# きのこクイズ

4〜5さいむけの、PCであそぶ いきもの きょういくゲームです。

- 🍄 きのこ：30しゅるい
- 🌱 しょくぶつ：40しゅるい
- 🪲 こんちゅう：29しゅるい

それぞれで、クイズ・たしざん・さがし・ずかんを あそべます。

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

くわしい仕様は `docs/SPEC.md` を みてください。
