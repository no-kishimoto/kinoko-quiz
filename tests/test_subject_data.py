from pathlib import Path

from data.subject_data import load_subject_names


ROOT = Path(__file__).parents[1]


def test_shokubutsu_selection_has_forty_unique_names():
    names = load_subject_names(ROOT / "data" / "shokubutsu.json")
    assert len(names) == 40
    assert len(names) == len(set(names))
    assert {"オクラ", "はえとりぐさ", "うつぼかずら", "モウセンゴケ", "サラセニア", "ブルーベリー"} <= set(names)
    assert {"しだ", "すみれ"}.isdisjoint(names)


def test_konchuu_selection_has_thirty_unique_names():
    names = load_subject_names(ROOT / "data" / "konchuu.json")
    assert len(names) == 30
    assert len(names) == len(set(names))
    assert {"カブトムシ", "ヘラクレスオオカブト", "コーカサスオオカブト", "オオゴンオニクワガタ"} <= set(names)
    assert {"クワガタムシ", "アカアシクワガタ", "コカブトムシ"}.isdisjoint(names)
    assert {"オニヤンマ", "アブラゼミ", "スズメバチ", "カナブン", "ハエ", "カ", "ニジイロクワガタ", "ギラファノコギリクワガタ", "ゴライアスオオツノハナムグリ"} <= set(names)
    assert {"トンボ", "セミ", "コガネムシ", "ガ", "ゴキブリ"}.isdisjoint(names)
