import type { Scene } from '@babylonjs/core/scene';
import type { GameAnimation } from './GameAnimation';

export class ParallelAnimation implements GameAnimation {
	readonly name: string;
	private _children: GameAnimation[];

	constructor(animations: GameAnimation[], name?: string) {
		this._children = animations;
		this.name = name ?? `Parallel(${animations.map((a) => a.name).join(', ')})`;
	}

	get duration(): number {
		return Math.max(0, ...this._children.map((a) => a.duration));
	}

	execute(scene: Scene): Promise<void> {
		return Promise.all(this._children.map((a) => a.execute(scene))).then(() => {});
	}

	cancel(): void {
		for (const child of this._children) child.cancel();
	}
}
