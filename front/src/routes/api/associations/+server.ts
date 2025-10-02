import { json } from '@sveltejs/kit';
import * as associationsDB from '$lib/server/associations/database.js';

export async function GET() {
    return json({ associations: associationsDB.getAllAssociations() });
}

export async function POST({ request }) {
    // Recogemos los datos como FormData
	const formData = await request.formData();

    const created_at = String(new Date().toISOString());
	const code = Number(formData.get('code'));
	const name = String(formData.get('name'));
    const description = String(formData.get('description'));
    const type = String(formData.get('type'));

    const association = associationsDB.createAssociation({
        created_at,
        code,
        name,
        description,
    });
    

    return json({ association }, { status: 201 });
}

// DELETE
export async function DELETE({ request }) {
    const { id } = await request.json();
    if (!id) {
        return json({ error: 'Missing id' }, { status: 400 });
    }

    const success = associationsDB.deleteAssociation(Number(id));
    if (!success) {
        return json({ error: 'Association not found' }, { status: 404 });
    }

    return json({ success: true });
}