import type { Scene } from '@babylonjs/core/scene';
import type { GameAnimation } from './GameAnimation';

export class AnimationPipeline {
	private _queue: GameAnimation[] = [];
	private _playing = false;
	private _currentAnimation: GameAnimation | null = null;
	private _scene: Scene;

	onQueueStarted: (() => void) | null = null;
	onQueueDrained: (() => void) | null = null;

	constructor(scene: Scene) {
		this._scene = scene;
	}

	get isPlaying(): boolean {
		return this._playing;
	}

	get queueLength(): number {
		return this._queue.length;
	}

	enqueue(animation: GameAnimation): void {
		this._queue.push(animation);
		if (!this._playing) this._processQueue();
	}

	enqueueBatch(animations: GameAnimation[]): void {
		this._queue.push(...animations);
		if (!this._playing) this._processQueue();
	}

	skipAll(): void {
		this._currentAnimation?.cancel();
		this._currentAnimation = null;
		this._queue.length = 0;
	}

	dispose(): void {
		this.skipAll();
		this.onQueueStarted = null;
		this.onQueueDrained = null;
	}

	private async _processQueue(): Promise<void> {
		if (this._playing) return;

		this._playing = true;
		this.onQueueStarted?.();

		while (this._queue.length > 0) {
			const animation = this._queue.shift()!;
			this._currentAnimation = animation;
			try {
				await animation.execute(this._scene);
			} catch (err) {
				console.warn(`Animation "${animation.name}" failed:`, err);
			}
			this._currentAnimation = null;
		}

		this._playing = false;
		this.onQueueDrained?.();
	}
}
