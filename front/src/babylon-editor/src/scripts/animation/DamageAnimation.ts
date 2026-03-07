import { Animation } from '@babylonjs/core/Animations/animation';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import type { Scene } from '@babylonjs/core/scene';
import type { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial';
import type { CardEntity } from '../entities/CardEntity';
import type { GameAnimation } from './GameAnimation';
import { ANIM_FPS, isMeshDisposed, msToFrames } from './utils';

const DEFAULT_DURATION_MS = 400;
const FLASH_COLOR = new Color3(1, 0.15, 0.1);
const SHAKE_AMPLITUDE = 2;
const SHAKE_CYCLES = 3;

export class DamageAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;

	private _entity: CardEntity;
	private _animatable: ReturnType<Scene['beginDirectAnimation']> | null = null;
	private _resolve: (() => void) | null = null;
	private _originalEmissive: Color3 | null = null;

	constructor(
		target: CardEntity,
		_damage: number,
		_remainingHealth: number,
		duration: number = DEFAULT_DURATION_MS,
	) {
		this._entity = target;
		this.duration = duration;
		this.name = `Damage(${target.instanceId})`;
	}

	execute(scene: Scene): Promise<void> {
		const mesh = this._entity.mesh;
		if (isMeshDisposed(mesh)) return Promise.resolve();

		const frames = msToFrames(this.duration);
		const animations: Animation[] = [];
		const baseX = mesh.position.x;

		// Shake: oscillate position.x
		const shakeAnim = new Animation(
			'dmgShake',
			'position.x',
			ANIM_FPS,
			Animation.ANIMATIONTYPE_FLOAT,
			Animation.ANIMATIONLOOPMODE_CONSTANT,
		);
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

		// Flash emissive red if using StandardMaterial
		const mat = mesh.material as StandardMaterial | null;
		if (mat && 'emissiveColor' in mat) {
			this._originalEmissive = mat.emissiveColor.clone();
			const flashAnim = new Animation(
				'dmgFlash',
				'material.emissiveColor',
				ANIM_FPS,
				Animation.ANIMATIONTYPE_COLOR3,
				Animation.ANIMATIONLOOPMODE_CONSTANT,
			);
			const midFrame = Math.round(frames * 0.3);
			flashAnim.setKeys([
				{ frame: 0, value: this._originalEmissive.clone() },
				{ frame: midFrame, value: FLASH_COLOR },
				{ frame: frames, value: this._originalEmissive.clone() },
			]);
			animations.push(flashAnim);
		}

		return new Promise<void>((resolve) => {
			this._resolve = resolve;
			this._animatable = scene.beginDirectAnimation(mesh, animations, 0, frames, false);
			this._animatable.onAnimationEndObservable.addOnce(() => {
				this._animatable = null;
				this._resolve = null;
				resolve();
			});
		});
	}

	cancel(): void {
		this._animatable?.stop();
		this._animatable = null;

		const mesh = this._entity.mesh;
		if (!isMeshDisposed(mesh)) {
			const mat = mesh.material as StandardMaterial | null;
			if (mat && this._originalEmissive && 'emissiveColor' in mat) {
				mat.emissiveColor = this._originalEmissive;
			}
		}

		this._resolve?.();
		this._resolve = null;
	}
}
