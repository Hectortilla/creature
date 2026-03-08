import type { Mesh } from "@babylonjs/core/Meshes/mesh";
import { scriptsDictionary, applyScriptOnObject } from "babylonjs-editor-tools";

/**
 * Clone a mesh and re-attach all of its editor scripts with their configured values.
 * Babylon's native clone() copies geometry/material/transforms but not editor scripts.
 */
export function cloneMeshWithScripts(source: Mesh, name: string): Mesh | null {
    const clone = source.clone(name);
    if (!clone) return null;

    const registered = scriptsDictionary.get(source);
    if (!registered?.length) return clone;

    for (const { instance: src } of registered) {
        const ctor = src.constructor as new (...args: any[]) => any;
        const dest = applyScriptOnObject(clone, ctor);

        // Copy editor-configured property values (tracked by @visibleAs* decorators)
        const inspectorProps: { propertyKey: string | symbol }[] =
            (ctor as any)._VisibleInInspector ?? [];
        for (const { propertyKey } of inspectorProps) {
            const key = propertyKey.toString();
            (dest as any)[key] = (src as any)[key];
        }
    }

    return clone;
}
