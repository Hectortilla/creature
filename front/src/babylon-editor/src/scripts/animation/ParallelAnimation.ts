import type { Scene } from '@babylonjs/core/scene';
import type { GameAnimation } from './GameAnimation';

export function parallel(...animations: GameAnimation[]): GameAnimation {
	return {
		name: `Parallel(${animations.map(a => a.name).join(', ')})`,
		duration: Math.max(0, ...animations.map(a => a.duration)),
		execute: (scene: Scene) => Promise.all(animations.map(a => a.execute(scene))).then(() => {}),
		cancel: () => animations.forEach(a => a.cancel()),
	};
}
