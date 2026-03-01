import { Mesh } from "@babylonjs/core/Meshes/mesh";

export default class MyScriptComponent {
    public constructor(public mesh: Mesh) { }

    public onStart(): void {
        // Do something when the script is loaded
    }

    public onUpdate(): void {

    }
}
