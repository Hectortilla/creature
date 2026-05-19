import type { Scene } from '@babylonjs/core/scene';

export interface GameAnimation {
	readonly name: string;
	readonly duration: number;
	execute(scene: Scene): Promise<void>;
	cancel(): void;
}
