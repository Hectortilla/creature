import type { GameAnimation } from './GameAnimation';

export function delay(ms: number): GameAnimation {
	let timerId: ReturnType<typeof setTimeout> | null = null;
	let resolve: (() => void) | null = null;

	return {
		name: `Delay(${ms}ms)`,
		duration: ms,
		execute: () => new Promise<void>(res => {
			resolve = res;
			timerId = setTimeout(() => { timerId = null; resolve = null; res(); }, ms);
		}),
		cancel: () => {
			if (timerId !== null) { clearTimeout(timerId); timerId = null; }
			resolve?.();
			resolve = null;
		},
	};
}
