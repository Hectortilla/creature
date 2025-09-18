import { json } from '@sveltejs/kit';
import * as attacksDB from '$lib/server/attacks/database.js';

export async function GET() {
    return json({ attacks: attacksDB.getAllAttacks() });
}

export async function POST({ request }) {
    // Recogemos los datos como FormData
	const formData = await request.formData();

    const created_at = String(new Date().toISOString());
	const code = Number(formData.get('code'));
	const name = String(formData.get('name'));
    const description = String(formData.get('description'));
	const element = Number(formData.get('element'));
    const type = String(formData.get('type'));
    const damage = Number(formData.get('damage'));
    const dice_rolls = Number(formData.get('dice_rolls'));
    const necessary_force = formData.get('necessary_force') !== null ? String(formData.get('necessary_force')) : null;
    const effect = formData.get('effect') ? String(formData.get('effect')): null;

    const attack = attacksDB.createAttack({
        created_at,
        code,
        name,
        description,
        element,
        type,
        damage,
        dice_rolls,
        necessary_force,
        effect
    });
    

    return json({ attack }, { status: 201 });
}

// DELETE
export async function DELETE({ request }) {
    const { id } = await request.json();
    if (!id) {
        return json({ error: 'Missing id' }, { status: 400 });
    }

    const success = attacksDB.deleteAttack(Number(id));
    if (!success) {
        return json({ error: 'Attack not found' }, { status: 404 });
    }

    return json({ success: true });
}