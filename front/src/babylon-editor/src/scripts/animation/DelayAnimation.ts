import type { Scene } from '@babylonjs/core/scene';
import type { GameAnimation } from './GameAnimation';

export class DelayAnimation implements GameAnimation {
	readonly name: string;
	readonly duration: number;
	private _timerId: ReturnType<typeof setTimeout> | null = null;
	private _resolve: (() => void) | null = null;

	constructor(duration: number) {
		this.duration = duration;
		this.name = `Delay(${duration}ms)`;
	}

	execute(_scene: Scene): Promise<void> {
		return new Promise<void>((resolve) => {
			this._resolve = resolve;
			this._timerId = setTimeout(() => {
				this._timerId = null;
				this._resolve = null;
				resolve();
			}, this.duration);
		});
	}

	cancel(): void {
		if (this._timerId !== null) {
			clearTimeout(this._timerId);
			this._timerId = null;
		}
		this._resolve?.();
		this._resolve = null;
	}
}
