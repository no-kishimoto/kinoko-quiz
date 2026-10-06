"""復元した生物を、問題中の3種類すべて生息環境に合わせて配置する。"""

import random

from src.dinosaur_search import load_dinosaur_search_assets
from src.search import create_search_session, status_text


def test_all_eighteen_species_use_matching_backgrounds_and_decoys_over_five_rounds():
    assets = load_dinosaur_search_assets()
    marine = {"plesiosaurus", "mosasaurus", "ammonite", "xiphactinus", "coelacanth", "trilobite", "anomalocaris", "ottoia"}
    assert {key for key, habitat in assets.habitats.items() if habitat == "sea"} == marine
    seen = set()
    backgrounds = set()
    for seed in range(100):
        rng = random.Random(seed)
        history = ()
        for index in range(5):
            session = create_search_session(
                assets.items, tuple(path for group in assets.living_backgrounds.values() for path in group), rng,
                current_index=index, mode="reconstruction", used_target_keys=history, unique_targets=True,
                habitats=assets.habitats, habitat_backgrounds=assets.living_backgrounds,
            )
            assert session.target.item.key not in history
            assert all(assets.habitats[p.item.key] == session.habitat for p in session.placements)
            assert session.background_path in assets.living_backgrounds[session.habitat]
            assert session.background_path.is_file()
            if session.habitat == "land":
                assert all(p.y >= 0.53 for p in session.placements)
            assert (session.background_path.stem == "primeval_sea") == (session.target.item.key in marine)
            assert "うみ" in status_text(session) if session.habitat == "sea" else "うみ" not in status_text(session)
            history = session.used_target_keys
            seen.add(session.target.item.key)
            backgrounds.add(session.background_path.stem)
        assert len(history) == len(set(history)) == 5
    assert seen == {item.key for item in assets.items}
    assert backgrounds == {"ancient_forest", "ancient_plain", "primeval_sea"}
