import { json } from '@sveltejs/kit';
import * as abilitiesDB from '$lib/server/abilities/database.js';

export async function GET() {
    return json({ abilities: abilitiesDB.getAllAbilities() });
}

export async function POST({ request }) {
    // Recogemos los datos como FormData
	const formData = await request.formData();

    const created_at = String(new Date().toISOString());
	const code = Number(formData.get('code'));
	const name = String(formData.get('name'));
    const description = String(formData.get('description'));
    const type = String(formData.get('type'));

    const ability = abilitiesDB.createAbility({
        created_at,
        code,
        name,
        description,
        type,
    });
    

    return json({ ability }, { status: 201 });
}

// DELETE
export async function DELETE({ request }) {
    const { id } = await request.json();
    if (!id) {
        return json({ error: 'Missing id' }, { status: 400 });
    }

    const success = abilitiesDB.deleteAbility(Number(id));
    if (!success) {
        return json({ error: 'Ability not found' }, { status: 404 });
    }

    return json({ success: true });
}