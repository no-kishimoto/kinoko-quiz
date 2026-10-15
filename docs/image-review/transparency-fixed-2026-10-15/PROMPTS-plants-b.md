# 植物 B：透過修正プロンプト

使用モード：built-in image_gen / background-extraction

## budou（ぶどう）

入力：`work/kinoko-quiz/assets/images/shokubutsu/zukan/budou.png`

`transparent_background: true`

```text
Use case: background-extraction. Input image 1 is the edit target: grape botanical illustration for an educational game. Change ONLY its background to genuine alpha transparency, including all white/light-gray/checkerboard leftovers trapped in gaps within leaf silhouettes, around curled tendrils and between stems and fruit. Preserve every grape, leaf, branch and fine tendril exactly in shape, position, proportion, color, shading and detailed illustration style. Preserve opaque pale highlights on the grapes. Any checker pattern is background, not part of the plant. Do not redraw or restyle, no added objects, no cast shadow, text or border. Output the same centered full plant composition as a clean transparent PNG cutout.
```

初回は接続エラー。主の指示で同じ built-in を1回再試行し成功。以降12種も同方式で成功。

## 共通条件

すべて `referenced_image_paths` に該当元画像1枚を指定し、`transparent_background: true` を指定。各入力と各出力を view_image で確認。出力PNGは生成元からコピーのみ。alpha加工・リサイズ・再描画は未実施。元画像・quiz・data・Gitは変更していない。

元画像ディレクトリ：`work/kinoko-quiz/assets/images/shokubutsu/zukan/`

保存ディレクトリ：`outputs/transparency-repair-2026-10-15/shokubutsu/`

生成元共通ディレクトリ：`<local-generated-images>/`

| 保存ファイル | 生成元ファイル |
| --- | --- |
| budou.png | exec-93474d78-ea19-4aa0-901b-4d2eede7300d.png |
| momo.png | exec-ecd9b116-0447-4ec5-99d9-542d1ef1240c.png |
| nashi.png | exec-3689aa89-353a-4341-9743-7594ab46cce8.png |
| suika.png | exec-52f53887-a0d9-4442-8668-bbdf09e855ee.png |
| meron.png | exec-201cb7a4-2724-454a-81d2-aef7c92aded8.png |
| kaki.png | exec-a1ae5854-95f6-48d4-92c0-8285aad30bfe.png |
| utsubokazura.png | exec-396efea4-9d46-4ae9-9ccd-bc8b4b7ab7a1.png |
| matsu.png | exec-981d53fa-9d12-4768-a46a-f720d75f7e20.png |
| ichou.png | exec-23330dc5-0aac-4798-ae8a-6282f8f6b2b9.png |
| momiji.png | exec-739aa701-c183-4b29-b994-a5c15874dedb.png |
| take.png | exec-f9489fe3-52fa-46c8-9907-80fffaee58ca.png |
| blueberry.png | exec-24f38551-03e2-4e34-af88-5c469c1fa8f0.png |
| mousengoke.png | exec-352f3645-8bd5-4fe8-9e0b-f48feeb3e518.png |

## momo（もも）

```text
Use case: background-extraction. Image 1 edit target is a peach branch botanical illustration. Remove only the white/light-gray/checkerboard background and ALL enclosed background in gaps between leaves, thin stems, branch and peaches, to genuine alpha transparency. Keep the two pink peaches, fuzzy pale skin highlights, every green leaf, vein, stem, wood texture, precise layout, scale, colors and detailed illustration style unchanged. Retain opaque pale peach fuzz and highlights, do not make the actual fruit translucent. No redraw, added object, shadow, text, border or checkerboard in the output. Same full composition, clean transparent PNG cutout.
```

## nashi（なし）

```text
Use case: background-extraction. Image 1 is the edit target: two Japanese pears hanging on a leafy branch. Change only the white/light-gray/checkerboard backdrop into true alpha transparency, including all enclosed gaps between leaves, stems and branch and both pears. Preserve both intact golden-brown pears, opaque white skin speckles and light reflections, every serrated green leaf and detailed veins, branches, stems, exact arrangement, shape, scale, framing, colors and illustration style. Do not crop or enlarge the subject. Do not redraw, add anything or leave pale background islands. No text, border, checkerboard or shadow. Clean genuinely transparent PNG cutout.
```

## suika（すいか）

```text
Use case: background-extraction. Image 1 edit target: complete watermelon vine with one striped green round fruit, yellow flower, lobed leaves, fine tendrils. Remove only white/light-gray/checkerboard background to true alpha transparency everywhere including trapped enclosed gaps between leaves, vine and fruit, tendril loops and small leaf cutouts. Keep opaque natural light green stripes, yellow petals, fine plant hairs and all actual plant parts. Preserve exact silhouette, layout, scale, framing, fruit color and all illustration detail unchanged. No crop, enlargement, redesign, added objects, shadow, text or border. Output same whole vine as clean transparent PNG.
```

## meron（メロン）

```text
Use case: background-extraction. Image 1 edit target: netted melon on vine, leaves, yellow flower and tendrils. Change ONLY white/light-gray/checkerboard background into genuine alpha transparency, including isolated enclosed gaps around stems, leaf notches and tendril loops. Preserve full fruit as opaque: the cream netting and pale green spaces within its net are real solid melon skin, never transparency. Preserve all leaves, hairs, yellow flower, vine, textures, colors, exact positioning and proportions. Same framing and detailed botanical illustration; no crop or zoom. No added elements, no redraw, no text, no shadow or border. Clean true transparent PNG cutout.
```

## kaki（かき）

```text
Use case: background-extraction. Image 1 edit target: three orange persimmons on leafy woody branch. Remove ONLY white/light-gray/checkerboard background to genuine alpha, especially all enclosed gaps among fruits, leaves, thin stems and branch. Keep three entire opaque orange fruits with pale highlights, green calyces, every green leaf and detailed veins, wood texture, shape, arrangement, exact scale, framing and botanical illustration style. No crop or zoom, no redraw or added parts, no pale background islands, no checkerboard, text, shadow or border. Same full composition on true transparent PNG.
```

## utsubokazura（うつぼかずら）

```text
Use case: background-extraction. Image 1 is the exact edit target: Nepenthes pitcher plant illustration, arching green leaves above THREE dangling red-yellow pitchers on fine long curved tendrils. Remove ONLY white/light-gray/checkerboard background to true alpha transparency. Critically remove ALL enclosed white/gray islands between curved leaves, tendrils, pitcher bodies and stems; these are background even when sealed by the plant outline. Preserve all THREE complete opaque pitchers with their lids, mouths, colored inner walls, fringes and markings, and preserve every fine connecting tendril, leaf, vein, all colors, layout, proportions, framing and illustration style. Do not turn the yellow inner pitcher walls into holes. No crop or zoom, no redesign or added plant parts, no text, border, shadow or visible checkerboard. Same centered plant on a clean genuine transparent PNG.
```

## matsu（まつ）

```text
Use case: background-extraction. Image 1 is the edit target: pine branch botanical illustration with two pinecones and many delicate green needles. Remove only white/light-gray/checkerboard background to true alpha, including ALL tiny enclosed gaps among pine needles and between branching limbs. Keep every needle connected, pointed and green, preserve both opaque pinecones and their pale scale highlights, woody trunk, exact arrangement, scale, framing, colors, texture and detailed botanical illustration. Do not remove light bark or cone highlights; do not merge the needles into solid foliage. No crop, zoom, redraw, added objects, shadow, text, border or checkerboard. Same full subject as clean transparent PNG.
```

## ichou（いちょう）

```text
Use case: background-extraction. Image 1 exact edit target is a ginkgo branch with fan-shaped green leaves and two pale yellow fruits. Change only the white/light-gray/checkerboard background into genuine alpha transparency, including ALL enclosed narrow spaces between curved leaf stems, leaves and woody branch. Preserve every opaque fan leaf and its fine parallel veins, both entire pale yellow fruits and their light highlights, leaf stems, wood texture, exact positions, shape, proportions, scale, framing and illustration style. The yellow fruits are solid, not background. No crop or zoom, redraw, extra objects, text, shadow, border or checkerboard. Same full subject as clean transparent PNG.
```

## momiji（もみじ）

```text
Use case: background-extraction. Image 1 exact edit target: red-orange Japanese maple leaves on a thin woody branch. Remove only the white/light-gray/checkerboard backdrop into genuine alpha transparency, including every enclosed background gap between crossing stems, leaves, their deep lobes and branch. Preserve all 7 intact palmate leaves with pointed serrated edges, fine veins, red/orange variation, thin red petioles, twig texture and exact composition, scale and framing. The light orange leaves and pale veins are plant tissue and must stay opaque. Do not crop, zoom, redraw, add or remove a leaf. No shadow, text, border or checker pattern. Same full illustration as clean true transparent PNG.
```

## take（たけ）

```text
Use case: background-extraction. Image 1 exact edit target: green bamboo culms with segmented nodes and thin pointed leaves. Remove only white/light-gray/checkerboard background to genuine alpha transparency, including all enclosed background between culms, leaf clusters and small thin branches. Preserve all bamboo stems, pale glossy highlights and node rims, leaf shape and veins, exact layout, number, colors, proportions, scale, framing and botanical illustration style. Light green culm highlights and cut tips are actual solid bamboo and must not become holes. Do not crop, zoom, redraw, add objects, shadow, text, border or checker pattern. Same complete bamboo illustration as clean transparent PNG.
```

## blueberry（ブルーベリー）

```text
Use case: background-extraction. Image 1 exact edit target: blueberry branch botanical illustration. Change only white/light-gray/checkerboard background into genuine alpha transparency, including all enclosed gaps between berries, crossing stems, leaves and woody branch. Preserve every opaque blue berry with pale powdery bloom and flower-end star, green leaves and veins, thin stems, wood texture, exact arrangement, scale, proportions, colors, framing and style. Pale berry bloom is solid skin not background. Do not crop, zoom, redraw or add elements. No shadow, text, border or visible checkerboard. Output same full detailed blueberry illustration as clean true transparent PNG.
```

## mousengoke（モウセンゴケ）

```text
Use case: background-extraction. Image 1 exact edit target: round rosette sundew with green spoon-shaped leaves, delicate red glandular tentacles and clear shiny dew droplets. Remove ONLY white/light-gray/checkerboard background to genuine alpha transparency, including all tiny isolated enclosed background spaces between leaf blades, thin tentacles and leaves behind the rosette. Crucially preserve every red tentacle, white fine hair on stems, bright white gleam and clear mucilage droplet; these are plant anatomy and highlights, not removable white background. Preserve opaque green leaves with fine texture, red-gold leaf blades, exact arrangement, scale, full framing, colors and illustration style. Restore any accidentally missing anatomical tiny strand in the same natural style, but do not add or redesign leaves. No crop, zoom, shadow, text, border or visible checkerboard. Same entire sundew as clean true transparent PNG.
```

## 目視と境界確認

全13種を view_image で確認。囲まれた白灰・市松背景の明白な残りは見当たらない。ぶどう、もも、なし、すいか、メロン、かき、ブルーベリーの果実、いちょうの黄色い実と葉、たけの明るい幹、モウセンゴケの白い毛・露の光沢は保持。

全13種のPNG実サイズは1254×1254。表示ツールの表示寸法ではなくPNG寸法で確認。全13種で上端・下端・左端・右端にalpha >128の画素は0。外縁近くの微小alphaによりbboxが0境界に触れるものはあるが、葉・枝・つるの本体が切れた様子は目視なし。ももの左下葉や、なしの左葉、モウセンゴケは元より余白が小さいため主側のカラー背景合成でも最終確認推奨。各輪郭に見える細い黄緑/赤の縁が濃色背景で目立つかも同様に最終確認推奨。
