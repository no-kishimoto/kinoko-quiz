from pathlib import Path

from data.subject_data import load_ready_subject_items, load_subject_names


ROOT = Path(__file__).parents[1]


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


def test_kyouryuu_selection_has_ten_unique_names():
    names = load_subject_names(ROOT / "data" / "kyouryuu.json")
    assert len(names) == 10
    assert len(names) == len(set(names))
    assert {
        "パキケファロサウルス",
        "ブラキオサウルス",
        "ティラノサウルス",
        "ステゴサウルス",
        "トリケラトプス",
        "プテラノドン",
        "プレシオサウルス",
        "モササウルス",
        "アンモナイト",
        "シファクティヌス",
    } == set(names)


def test_all_ten_prehistoric_animals_are_ready_for_games():
    items = load_ready_subject_items(ROOT / "data" / "kyouryuu.json")
    assert len(items) == 10
    assert items[0].name == "パキケファロサウルス"
    assert items[-1].name == "シファクティヌス"
