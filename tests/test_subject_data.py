import json
from pathlib import Path

from data.subject_data import load_ready_subject_items, load_subject_names


ROOT = Path(__file__).parents[1]
KYOURYUU_NAMES = (
    "パキケファロサウルス", "ブラキオサウルス", "ティラノサウルス",
    "ステゴサウルス", "トリケラトプス", "プテラノドン", "プレシオサウルス",
    "モササウルス", "アンモナイト", "シファクティヌス",
    "シーラカンス", "アンキロサウルス", "パラサウロロフス", "サンヨウチュウ",
    "アノマロカリス", "オットイア", "マンモス", "スミロドン",
)
EXISTING_KYOURYUU_TEXT = (
    ("あたまが ぶあつく まるい。", "あたまの うえが とても かたい きょうりゅう。なかまと あたまを くらべたかも しれないよ。"),
    ("とても ながい くび。まえあしが ながい。", "とても おおきな くさを たべる きょうりゅう。ながい くびで たかい きの はを たべたよ。"),
    ("おおきな あたまと するどい は。", "とても おおきな にくを たべる きょうりゅう。つよい あしで あるいたよ。"),
    ("せなかに おおきな いた。しっぽに とげ。", "せなかに ならんだ いたが めじるしの くさを たべる きょうりゅう。しっぽの とげで じぶんを まもったよ。"),
    ("かおに 3ぼんの つの。おおきな えり。", "3ぼんの つのと おおきな えりが かっこいい くさを たべる きょうりゅう。"),
    ("ながい くちばしと おおきな はね。", "そらを とんだ むかしの はちゅうるい。きょうりゅうとは ちがう なかまだよ。"),
    ("とても ながい くび。ひれみたいな あし。", "うみを およいだ むかしの はちゅうるい。きょうりゅうとは ちがう なかまだよ。"),
    ("おおきな くちと するどい は。", "うみを およいだ とても おおきな はちゅうるい。きょうりゅうとは ちがう なかまだよ。"),
    ("うずまきの かたちの から。", "うみで くらした むかしの いきもの。うずまきの からが めじるしだよ。"),
    ("おおきな くちと とがった は。", "むかしの うみを およいだ おおきな さかな。きょうりゅうとは ちがう なかまだよ。"),
)
APPROVED_ADDITION_HINTS = {
    "coelacanth": "ひれの つけねが ふとい。",
    "ankylosaurus": "かたい よろい。しっぽの さきに おおきな かたまり。",
    "parasaurolophus": "あたまから うしろへ のびる ながい とさか。",
    "trilobite": "からだに たくさんの ふし。そとが かたい から。",
    "anomalocaris": "おおきな め。からだの よこに ならぶ ひれ。",
    "ottoia": "ながい からだに たくさんの しわ。",
    "mammoth": "ながく まがった 2ほんの きば。4ほんの あし。",
    "smilodon": "うえの あごから のびる ながい 2ほんの きば。",
}


def test_shokubutsu_selection_has_forty_unique_names():
    names = load_subject_names(ROOT / "data" / "shokubutsu.json")
    assert len(names) == 40
    assert len(names) == len(set(names))
    assert {"オクラ", "はえとりぐさ", "うつぼかずら", "モウセンゴケ", "サラセニア", "ブルーベリー"} <= set(names)
    assert {"しだ", "すみれ"}.isdisjoint(names)


def test_all_forty_plants_are_ready_for_games():
    items = load_ready_subject_items(ROOT / "data" / "shokubutsu.json")
    assert len(items) == 40
    assert items[0].name == "さくら"
    assert items[9].name == "どんぐり"
    assert items[-1].name == "ブルーベリー"


def test_konchuu_selection_has_twenty_nine_unique_names():
    names = load_subject_names(ROOT / "data" / "konchuu.json")
    assert len(names) == 29
    assert len(names) == len(set(names))
    assert {"カブトムシ", "ヘラクレスオオカブト", "コーカサスオオカブト", "オウゴンオニクワガタ"} <= set(names)
    assert {"クワガタムシ", "アカアシクワガタ", "コカブトムシ", "ヒラタクワガタ", "オオゴンオニクワガタ"}.isdisjoint(names)
    assert {"オニヤンマ", "アブラゼミ", "スズメバチ", "カナブン", "ハエ", "カ", "ニジイロクワガタ", "ギラファノコギリクワガタ", "ゴライアスオオツノハナムグリ"} <= set(names)
    assert {"トンボ", "セミ", "コガネムシ", "ガ", "ゴキブリ"}.isdisjoint(names)


def test_all_twenty_nine_insects_are_ready_for_games():
    items = load_ready_subject_items(ROOT / "data" / "konchuu.json")
    assert len(items) == 29
    assert items[0].name == "カブトムシ"
    assert items[-1].name == "ゴライアスオオツノハナムグリ"


def test_kyouryuu_selection_has_eighteen_unique_names_in_approved_order():
    names = load_subject_names(ROOT / "data" / "kyouryuu.json")
    assert len(names) == 18
    assert len(names) == len(set(names))
    assert names == KYOURYUU_NAMES


def test_all_eighteen_prehistoric_animals_are_ready_for_games():
    items = load_ready_subject_items(ROOT / "data" / "kyouryuu.json")
    assert len(items) == 18
    assert len({item.key for item in items}) == 18
    assert tuple(item.name for item in items) == KYOURYUU_NAMES
    assert tuple((item.quiz_hint, item.zukan_text) for item in items[:10]) == EXISTING_KYOURYUU_TEXT


def test_new_game_entries_use_the_approved_candidate_text_and_order():
    items = load_ready_subject_items(ROOT / "data" / "kyouryuu.json")
    candidates = json.loads((ROOT / "data" / "kyouryuu_candidates.json").read_text())

    assert len(candidates) == 8
    assert tuple(item.key for item in items[10:]) == tuple(item["key"] for item in candidates)
    assert {item.key: item.quiz_hint for item in items[10:]} == APPROVED_ADDITION_HINTS
    for item, candidate in zip(items[10:], candidates, strict=True):
        assert (item.name, item.quiz_hint, item.zukan_text) == (
            candidate["name"], candidate["quiz_hint"], candidate["zukan_text"],
        )
        assert candidate["description_status"] == "approved"
        assert candidate["image_status"] == "approved"
        assert candidate["quiz_hint_status"] == "approved"
        assert candidate["quiz_hint_approval_date"] == "2026-10-14"
