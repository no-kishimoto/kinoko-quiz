# 昆虫・透過修正の使用プロンプト

方式: built-in image_gen。各対象を view_image で表示し、referenced_image_paths に原画1枚、transparent_background=true を指定。生成PNGのalphaは加工せず保持。

## suzumebachi

Use case: background-extraction and localized restoration.
Asset type: an existing educational insect game PNG. Image 1 is the edit target, a Japanese hornet illustration.
Primary request: Correct transparency only. Produce an actual transparent-background PNG, not a painted checkerboard. Preserve the exact insect, pose, colors, detailed texture, scale, framing, every leg and antenna. Remove all remaining white/gray/checkerboard background between legs or body. Restore the accidentally erased ragged transparent holes along the lower-right edge of the large upper wing: make a continuous naturally translucent pale amber wing membrane with the existing fine veins, matching adjacent wing, without changing its shape or adding a wing.
Constraints: Insect body must remain opaque; retain white highlights and natural wing membrane (do not treat them as background). No restyling, recentering, text, borders, shadows, extra insects or props. Outside the insect and inside genuine gaps must be transparent. Keep the original illustration otherwise unchanged.

## ari

Use case: background-extraction. Image 1 is the edit target, the existing black ant educational illustration. Correct transparency ONLY: cut out ALL white/gray checkerboard background including the enclosed triangular gaps between the raised rear legs, between the head and foreleg and the little gaps between thorax/body and legs. Output a genuine transparent PNG with alpha, no painted checkerboard. Keep every pixel of the ant's design as close as possible: same six thin jointed legs, antennae, hairs, eyes, mandibles, three body sections, black glossy color, texture, side-facing-left pose, scale and canvas framing. Keep natural pale highlights opaque. Do not redesign or simplify the insect, add/delete legs, shift composition or crop it. Remove background inside genuine leg gaps as carefully as outside. No text, border, shadow or additional objects.

## koorogi

Use case: background-extraction. Image 1 is the edit target: the existing brown cricket illustration. Make a clean cutout with a genuine transparent PNG alpha background. Remove ALL residual white/gray/checkerboard background, especially the enclosed triangular hole inside the raised far hind leg above the back, the spaces between forelegs and thorax, and the smaller enclosed near-hind-leg gaps. Keep the cricket itself unchanged: exact brown colors and glossy texture, existing wing veins, long complete antennae, thin jointed legs and spines, eyes and mouthparts, side-facing-left pose, scale, framing and composition. Preserve pale highlights and all insect anatomy opaque. No extra legs, no removal of legs or hairs, no new details or restyling. No checkerboard pixels or white patches left in empty leg gaps, no text or extra objects.

## kamakiri

Use case: background-extraction. Input image is the edit target: the existing educational insect illustration. Fix transparency only; return an actual transparent PNG cutout. Remove the white/gray checkerboard patch enclosed inside the folded spiny forelegs (the triangular opening of the grasping mantis forelegs), as well as all other genuine gaps between legs, body and antennae. Keep all spines, thin legs and complete fine antennae. Preserve the original insect shape, pose, anatomy, green/yellow colors, detailed texture, lighting, scale and framing exactly. All natural white highlights and pale insect body parts must remain visible; do not mistake them for background. Do not add or delete insect parts, restyle, reposition, crop, add objects, text or shadow. No white/gray/checkerboard pixels in the empty internal gaps or outside the insect.

生成元: <local-generated-images>/exec-622487fd-6165-45ff-9295-10c9aae30eb8.png

## batta

Use case: background-extraction. Input image is the edit target: the existing educational insect illustration. Fix transparency only; return an actual transparent PNG cutout. Remove the white/gray checkerboard triangles enclosed inside BOTH raised folded hind legs above the back, plus all other genuine gaps between legs and body. Keep complete jointed legs, femur ridges, thin tibiae and spines, antennae and wing veins. Preserve the original insect shape, pose, anatomy, green/yellow colors, detailed texture, lighting, scale and framing exactly. All natural white highlights and pale insect body parts must remain visible; do not mistake them for background. Do not add or delete insect parts, restyle, reposition, crop, add objects, text or shadow. No white/gray/checkerboard pixels in the empty internal gaps or outside the insect.

生成元: <local-generated-images>/exec-e8740f07-2aa1-4a32-b502-db341100fb81.png

## ka

Use case: background-extraction. Image 1 is the existing mosquito illustration and is the edit target. Correct background transparency only. Make ALL white/gray/checkerboard background fully transparent, particularly the triangular enclosed openings between the thin raised legs above the thorax, body-leg gaps, and all empty spaces around the long legs, proboscis and antennae. Retain the actual pale translucent wings with their fine veins as continuous complete membranes; do not punch holes in or remove wings. Preserve the exact six very thin jointed legs and all fine hairs, long mouthpart, antennae, striped brown body, pose, detailed existing texture, scale, orientation and canvas framing. Retain natural white or pale highlights. Output a genuinely transparent-background PNG, no checkerboard artwork, text, added objects, cast shadow, restyling, added/deleted body parts, or cropping.

生成元: <local-generated-images>/exec-08cc82d2-59f4-48ba-b311-663d5d499863.png

## girafanokogirikuwagata

Use case: background-extraction. Image 1 is the edit target, the existing long-jawed giraffe stag beetle educational illustration. Keep this exact beetle unchanged in anatomy, exceptionally long serrated mandibles, brown/gold colors, jointed legs, texture, viewpoint, pose, scale and framing. Correct transparency only: remove any remaining opaque white/gray checkerboard background INCLUDING the small triangular empty space enclosed between the upper bent front leg and the thorax on the upper-right of the body. Preserve the actual bright reflected highlights on the beetle, its legs and mandibles; do not erase pale insect parts. All genuine empty gaps and exterior background must be truly transparent using PNG alpha, not a drawn checkerboard. No changes to the beetle design, new objects, text, shadow, crop, or repositioning.

生成元: <local-generated-images>/exec-068e9620-16bd-432a-8c50-0aba1ae301e5.png
