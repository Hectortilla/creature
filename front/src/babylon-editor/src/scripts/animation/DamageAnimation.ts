import { Animation } from '@babylonjs/core/Animations/animation';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import type { Scene } from '@babylonjs/core/scene';
import type { Animatable } from '@babylonjs/core/Animations/animatable';
import type { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const FLASH_COLOR = new Color3(1, 0.15, 0.1);
const SHAKE_AMPLITUDE = 2;
const SHAKE_CYCLES = 3;

export function damageShake(target: CardEntity, duration = 400): GameAnimation {
	let animatable: Animatable | null = null;
	let resolve: (() => void) | null = null;
	let originalEmissive: Color3 | null = null;

	return {
		name: `Damage(${target.instanceId})`,
		duration,

		execute(scene: Scene) {
			const mesh = target.mesh;
			if (isMeshDisposed(mesh)) return Promise.resolve();

			const frames = msToFrames(duration);
			const animations: Animation[] = [];
			const baseX = mesh.position.x;

			// Shake: oscillate position.x with decay
			const shakeAnim = new Animation('dmgShake', 'position.x', ANIM_FPS, Animation.ANIMATIONTYPE_FLOAT, Animation.ANIMATIONLOOPMODE_CONSTANT);
			const shakeKeys: { frame: number; value: number }[] = [{ frame: 0, value: baseX }];
			for (let i = 1; i <= SHAKE_CYCLES * 2; i++) {
				const f = Math.round((i / (SHAKE_CYCLES * 2)) * frames);
				const dir = i % 2 === 1 ? 1 : -1;
				const decay = 1 - i / (SHAKE_CYCLES * 2 + 1);
				shakeKeys.push({ frame: f, value: baseX + dir * SHAKE_AMPLITUDE * decay });
			}
			shakeKeys.push({ frame: frames, value: baseX });
			shakeAnim.setKeys(shakeKeys);
			animations.push(shakeAnim);

			// Flash emissive red if StandardMaterial
			const mat = mesh.material as StandardMaterial | null;
			if (mat && 'emissiveColor' in mat) {
				originalEmissive = mat.emissiveColor.clone();
				const flashAnim = new Animation('dmgFlash', 'material.emissiveColor', ANIM_FPS, Animation.ANIMATIONTYPE_COLOR3, Animation.ANIMATIONLOOPMODE_CONSTANT);
				flashAnim.setKeys([
					{ frame: 0, value: originalEmissive.clone() },
					{ frame: Math.round(frames * 0.3), value: FLASH_COLOR },
					{ frame: frames, value: originalEmissive.clone() },
				]);
				animations.push(flashAnim);
			}

			return new Promise<void>(res => {
				resolve = res;
				animatable = scene.beginDirectAnimation(mesh, animations, 0, frames, false);
				animatable.onAnimationEndObservable.addOnce(() => { animatable = null; resolve = null; res(); });
			});
		},

		cancel() {
			animatable?.stop();
			animatable = null;
			if (!isMeshDisposed(target.mesh)) {
				const mat = target.mesh.material as StandardMaterial | null;
				if (mat && originalEmissive && 'emissiveColor' in mat) mat.emissiveColor = originalEmissive;
			}
			resolve?.();
			resolve = null;
		},
	};
}
