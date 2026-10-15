# 植物・昆虫の透過修正（2026-10-15）

植物40種類・昆虫29種類を点検し、植物26種類・昆虫7種類の原画と、それぞれのクイズ画像を更新しました（33種類・66枚）。未修正の植物14種類・昆虫22種類、計72枚は、バックアップとバイト単位で一致しています。ゲームの種類・問題数・説明文・操作・ヒント位置は変更していません。Godotへの新しい分野の導入も行っていません。

## 修正前後の画像

各カードは、左が修正前、中央が修正後、右が修正後のクイズです。青い部分が背景の透過です。

- [植物01〜10](shokubutsu-1.jpg)
- [植物11〜20](shokubutsu-2.jpg)
- [植物21〜26](shokubutsu-3.jpg)
- [昆虫7種類](konchuu-1.jpg)
- [アリ・コオロギ・スズメバチの拡大比較（ゲームの背景色）](insects-before-after.jpg)

## 修正内容

- 葉・枝・つるや、昆虫の脚に囲まれた白／灰色／市松模様の背景を取り除きました。
- スズメバチの大きな翅にあった透明な欠けを、翅脈と淡い翅膜を含めて復元しました。
- 白い花、たんぽぽの綿毛、モウセンゴケの毛と露、昆虫の翅や体の光沢は保持しました。
- 細い茎、巻きひげ、根、脚、触角、大顎の大きな欠けがないことを比較画像で確認しています。

## 使用した画像編集方式とプロンプト

imagegenスキルに従い、内蔵の `image_gen` を使いました。各原画を参照した `background-extraction` 編集で、透過背景を指定しています。CLI/APIフォールバックや、色のしきい値による背景の一括削除は使っていません。生成PNGのアルファチャンネル・寸法は加工せず、選んだ出力をそのまま原画に採用しました。

- [植物A：13種類のプロンプト・生成元対応](PROMPTS-plants-a.md)
- [植物B：13種類のプロンプト・生成元対応](PROMPTS-plants-b.md)
- [昆虫7種類のプロンプト](PROMPTS-insects.md)

一部の出力には、輪郭や背景にアルファ値1/255程度の極小値があります。元のアルファを一括しきい値加工せず保持し、青色とゲームの薄黄色で通常合成して、目立つ残り背景やフリンジがないことを確認しました。最低条件の検査は四隅0〜1/255を許容しますが、不透明な背景や空の画像は拒否します。

## 保存先

原画は `assets/images/shokubutsu/zukan/` と `assets/images/konchuu/zukan/`、対応クイズはそれぞれの `quiz/` に保存しています。以下はゲームが参照する実ファイルです。

| 分野 | 種類 | 原画 | クイズ |
|---|---|---|---|
| 植物 | たんぽぽ | [PNG](../../../assets/images/shokubutsu/zukan/tanpopo.png) | [PNG](../../../assets/images/shokubutsu/quiz/tanpopo.png) |
| 植物 | あさがお | [PNG](../../../assets/images/shokubutsu/zukan/asagao.png) | [PNG](../../../assets/images/shokubutsu/quiz/asagao.png) |
| 植物 | ねこじゃらし | [PNG](../../../assets/images/shokubutsu/zukan/nekopanjya.png) | [PNG](../../../assets/images/shokubutsu/quiz/nekopanjya.png) |
| 植物 | トマト | [PNG](../../../assets/images/shokubutsu/zukan/tomato.png) | [PNG](../../../assets/images/shokubutsu/quiz/tomato.png) |
| 植物 | きゅうり | [PNG](../../../assets/images/shokubutsu/zukan/kyuuri.png) | [PNG](../../../assets/images/shokubutsu/quiz/kyuuri.png) |
| 植物 | じゃがいも | [PNG](../../../assets/images/shokubutsu/zukan/jagaimo.png) | [PNG](../../../assets/images/shokubutsu/quiz/jagaimo.png) |
| 植物 | ピーマン | [PNG](../../../assets/images/shokubutsu/zukan/piiman.png) | [PNG](../../../assets/images/shokubutsu/quiz/piiman.png) |
| 植物 | えだまめ | [PNG](../../../assets/images/shokubutsu/zukan/edamame.png) | [PNG](../../../assets/images/shokubutsu/quiz/edamame.png) |
| 植物 | オクラ | [PNG](../../../assets/images/shokubutsu/zukan/okura.png) | [PNG](../../../assets/images/shokubutsu/quiz/okura.png) |
| 植物 | りんご | [PNG](../../../assets/images/shokubutsu/zukan/ringo.png) | [PNG](../../../assets/images/shokubutsu/quiz/ringo.png) |
| 植物 | みかん | [PNG](../../../assets/images/shokubutsu/zukan/mikan.png) | [PNG](../../../assets/images/shokubutsu/quiz/mikan.png) |
| 植物 | バナナ | [PNG](../../../assets/images/shokubutsu/zukan/banana.png) | [PNG](../../../assets/images/shokubutsu/quiz/banana.png) |
| 植物 | いちご | [PNG](../../../assets/images/shokubutsu/zukan/ichigo.png) | [PNG](../../../assets/images/shokubutsu/quiz/ichigo.png) |
| 植物 | ぶどう | [PNG](../../../assets/images/shokubutsu/zukan/budou.png) | [PNG](../../../assets/images/shokubutsu/quiz/budou.png) |
| 植物 | もも | [PNG](../../../assets/images/shokubutsu/zukan/momo.png) | [PNG](../../../assets/images/shokubutsu/quiz/momo.png) |
| 植物 | なし | [PNG](../../../assets/images/shokubutsu/zukan/nashi.png) | [PNG](../../../assets/images/shokubutsu/quiz/nashi.png) |
| 植物 | すいか | [PNG](../../../assets/images/shokubutsu/zukan/suika.png) | [PNG](../../../assets/images/shokubutsu/quiz/suika.png) |
| 植物 | メロン | [PNG](../../../assets/images/shokubutsu/zukan/meron.png) | [PNG](../../../assets/images/shokubutsu/quiz/meron.png) |
| 植物 | かき | [PNG](../../../assets/images/shokubutsu/zukan/kaki.png) | [PNG](../../../assets/images/shokubutsu/quiz/kaki.png) |
| 植物 | うつぼかずら | [PNG](../../../assets/images/shokubutsu/zukan/utsubokazura.png) | [PNG](../../../assets/images/shokubutsu/quiz/utsubokazura.png) |
| 植物 | まつ | [PNG](../../../assets/images/shokubutsu/zukan/matsu.png) | [PNG](../../../assets/images/shokubutsu/quiz/matsu.png) |
| 植物 | いちょう | [PNG](../../../assets/images/shokubutsu/zukan/ichou.png) | [PNG](../../../assets/images/shokubutsu/quiz/ichou.png) |
| 植物 | もみじ | [PNG](../../../assets/images/shokubutsu/zukan/momiji.png) | [PNG](../../../assets/images/shokubutsu/quiz/momiji.png) |
| 植物 | たけ | [PNG](../../../assets/images/shokubutsu/zukan/take.png) | [PNG](../../../assets/images/shokubutsu/quiz/take.png) |
| 植物 | ブルーベリー | [PNG](../../../assets/images/shokubutsu/zukan/blueberry.png) | [PNG](../../../assets/images/shokubutsu/quiz/blueberry.png) |
| 植物 | モウセンゴケ | [PNG](../../../assets/images/shokubutsu/zukan/mousengoke.png) | [PNG](../../../assets/images/shokubutsu/quiz/mousengoke.png) |
| 昆虫 | アリ | [PNG](../../../assets/images/konchuu/zukan/ari.png) | [PNG](../../../assets/images/konchuu/quiz/ari.png) |
| 昆虫 | コオロギ | [PNG](../../../assets/images/konchuu/zukan/koorogi.png) | [PNG](../../../assets/images/konchuu/quiz/koorogi.png) |
| 昆虫 | カマキリ | [PNG](../../../assets/images/konchuu/zukan/kamakiri.png) | [PNG](../../../assets/images/konchuu/quiz/kamakiri.png) |
| 昆虫 | バッタ | [PNG](../../../assets/images/konchuu/zukan/batta.png) | [PNG](../../../assets/images/konchuu/quiz/batta.png) |
| 昆虫 | カ | [PNG](../../../assets/images/konchuu/zukan/ka.png) | [PNG](../../../assets/images/konchuu/quiz/ka.png) |
| 昆虫 | スズメバチ | [PNG](../../../assets/images/konchuu/zukan/suzumebachi.png) | [PNG](../../../assets/images/konchuu/quiz/suzumebachi.png) |
| 昆虫 | ギラファノコギリクワガタ | [PNG](../../../assets/images/konchuu/zukan/girafanokogirikuwagata.png) | [PNG](../../../assets/images/konchuu/quiz/girafanokogirikuwagata.png) |

## 安全なクイズ画像の再生成

[`scripts/rebuild_subject_quiz_assets.py`](../../../scripts/rebuild_subject_quiz_assets.py) を追加しました。確認済み原画のRGB・透明度を変更せず、指定したカラー円の位置を使ってクイズだけ再生成します。全入力を確認してから出力を置き換え、同じピクセルのファイルは書き換えません。`--check` はファイルを変更しません。

旧 `remove_white_background.py` は、通常実行では画像を変更せず終了するよう安全化しました。白い花や翅を消し得る旧方式を、今回の画像に再実行してはいけません。

## 検証記録

- 最終状態で `pytest -q`：192件すべて成功。植物・昆虫のクイズ再生成確認も、ともに差分0件。
- 全69種類の図鑑・クイズの最低アルファ条件と、両画像の透明度一致を検証。
- 画像編集後の実画像で、脚・葉間の12地点と、復元したスズメバチの翅2地点、たんぽぽの白い綿毛1地点を、図鑑とクイズの双方で回帰テスト。
- 白・灰・薄青の本体と、閉じた透明な隙間、半透明の輪郭を含む合成サンプルで、元の透明度がPNG保存後まで維持されることを検証。
- 新しい再生成経路が原画を変更しないこと、検査モードや入力不足時に画像を書き換えないことを検証。
- 修正PNGは生成元とバイト単位で同一。[反映状況とSHA-256](repair-manifest.json) を保存。

これは画像の透過と既存機能の確認です。生物学的な全細部を新たに監修したという意味ではありません。起動中のアプリは再起動すると差し替えが確実に反映されます。この記録はローカル画像修正時点のもので、GitHubへの反映とColabの更新・再起動は別工程です。

## 修正前の控え

ローカルの `<local-workspace>/outputs/transparency-repair-2026-10-15/backup/` に、修正前の植物・昆虫の図鑑／クイズ画像を保管しています。生成候補・採用元・反映後のハッシュ記録も同じ親フォルダに保存しています。既存の `plant-transparency-2026-10-15` / `insect-transparency-2026-10-15` の一覧JPGは修正前の記録です。
