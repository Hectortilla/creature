import { Mesh } from "@babylonjs/core/Meshes/mesh";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";

import { IScript, visibleAsNumber } from "babylonjs-editor-tools";

export default class HoverAnimation implements IScript {
	@visibleAsNumber("Hover Speed", {
		min: 0,
		max: 5,
	})
	private _speed: number = 200;

	@visibleAsNumber("Hover Height", {
		min: 0,
		max: 2,
	})
	private _height: number = 5;

	private _time: number = 0;
	private _startY: number = 0;

	public constructor(public mesh: Mesh) {}

	public onStart(): void {
		// Store the original Y position
		this._startY = this.mesh.position.y;
	}

	public onUpdate(): void {
		const ratio = this.mesh.getScene().getAnimationRatio();

		// Update time
		this._time += this._speed * ratio;

		// Hover motion (sin wave)
		this.mesh.position.y = this._startY + Math.sin(this._time) * this._height;
	}
}