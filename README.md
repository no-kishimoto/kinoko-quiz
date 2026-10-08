# きのこクイズ

4〜5さいむけの、PCであそぶ いきもの きょういくゲームです。

- 🍄 きのこ：30しゅるい
- 🌱 しょくぶつ：40しゅるい
- 🪲 こんちゅう：29しゅるい
- 🦖 きょうりゅう：10しゅるい

それぞれで、クイズ・たしざん・ひきざん・さがし・ずかんを あそべます。

クイズは5もんか10もん、けいさんは10もん、さがしは5もんです。けいさんのさいごの3もんは、かんすうじでも あそべます。

完成を目指しているのは、Python・Gradio版です。Godot版の試作は [godot/README.md](godot/README.md) に残しています。

🦖 きょうりゅうには、18しゅるいの ほねや かせきを さがす「かせきさがし」を Gradioで ついかしました。ちそうの はいけいは 2まい、1かい 5もんです。せいかいで ピンポンが なり、「つぎの もんだい」で すすみます。

「きょうりゅうさがし」では、18しゅるいの ふくげんがぞうを さがせます。うみの いきものは「たいこの うみ」、りくの いきものは「こだいの もり」か「こだいの へいげん」に でます。1かい 5もんで、おなじ いきものは くりかえし でません。きょうりゅうの クイズと ずかんは、いまは 10しゅるいの ままです。


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

PCブラウザでの確認項目は [Gradio版の動作確認](docs/GRADIO_CHECKLIST.md) にまとめています。

## Googleドライブ・Colabでの起動

家庭で使うコード・画像・音声・資料の原本をGoogleドライブで管理する。

1. 初回だけ[移行用ノートブック](https://colab.research.google.com/github/no-kishimoto/kinoko-quiz/blob/main/colab/migrate_to_drive.ipynb)を開き、上から実行する。
2. 「移行完了」の後、ドライブ内の `kinoko_quiz/kinoko-quiz/colab/launch_kinoko_quiz.ipynb` をGoogle Colaboratoryで開く。
3. 最初のセルに「準備完了」が出たら起動セルを実行し、今回表示された新しいURLを開く。

以後はドライブに保存されたノートブックだけで起動でき、GitHubからコードや画像を取得しない。ライブラリのインストールと共有URLにはインターネット接続が必要。ゲームで遊ぶ間は起動セルを実行中にする。

[移行・編集・バックアップの手順](docs/GOOGLE_DRIVE.md)を参照。以前Googleドライブへコピーした起動ノートブックは自動更新されないため、移行後は上記の新しいファイルを使う。

くわしい仕様は `docs/SPEC.md` を みてください。
