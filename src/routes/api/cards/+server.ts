import { json } from '@sveltejs/kit';
import * as cardsDB from '$lib/server/cards/database';
import path from 'path';
import fs from 'fs';


// GET
export async function GET() {
	return json({ cards: cardsDB.getAllCards() });
}

// POST
export async function POST({ request }) {
	// Recogemos los datos como FormData
	const formData = await request.formData();

	// Campos de texto
	const created_at = String(new Date().toISOString());
	const code = Number(formData.get('code'));
	const name = String(formData.get('name'));
	const is_evolution =
		formData.get('is_evolution') !== null
		&& formData.get('is_evolution') !== 'null'
		? Number(formData.get('is_evolution'))
		: null;
	const next_evolution = Number(formData.get('next_evolution')) !== null ? Number(formData.get('next_evolution')) : null;
	const description = String(formData.get('description'));
	const first_element = Number(formData.get('first_element'));
	const second_element = formData.get('second_element') !== null ? Number(formData.get('second_element')) : null;
	const type = Number(formData.get('type'));
	const character = Number(formData.get('character'));
	const first_attack= formData.get('first_attack') !== null ? Number(formData.get('first_attack')) : null;
	const second_attack= formData.get('second_attack') !== null ? Number(formData.get('second_attack')) : null;
	const health = Number(formData.get('health'));
	const physical_defence = Number(formData.get('physical_defence'));
	const magic_defence = Number(formData.get('magic_defence'));
	const forces = formData.get('forces') !== null ? String(formData.get('forces')) : null;
	const ability= formData.get('ability') !== null ? Number(formData.get('ability')) : null;
	const association= formData.get('association') !== null ? Number(formData.get('association')) : null;

	// Campo de imagen (archivo)
	const image = formData.get('image'); // puede ser File o null
	let imagePath: string | null = null;

	if (image && image instanceof File) {
		const buffer = Buffer.from(await image.arrayBuffer());
		const uploadDir = path.join(process.cwd(), 'static', 'uploads');

		// crear carpeta si no existe
		if (!fs.existsSync(uploadDir)) {
			fs.mkdirSync(uploadDir, { recursive: true });
		}

		// Guardar archivo en /static/uploads/
		const filePath = path.join(uploadDir, image.name);
		fs.writeFileSync(filePath, buffer);

		// Ruta accesible públicamente
		imagePath = `/uploads/${image.name}`;
	}

	// Campo de imagen overlay (archivo)
	const imageOverlay = formData.get('overlay_image'); // puede ser File o null
	let imageOverlayPath: string | null = null;

	if (imageOverlay && imageOverlay instanceof File) {
		const buffer = Buffer.from(await imageOverlay.arrayBuffer());
		const uploadDir = path.join(process.cwd(), 'static', 'uploads');

		// crear carpeta si no existe
		if (!fs.existsSync(uploadDir)) {
			fs.mkdirSync(uploadDir, { recursive: true });
		}

		// Guardar archivo en /static/uploads/
		const filePath = path.join(uploadDir, imageOverlay.name);
		fs.writeFileSync(filePath, buffer);

		// Ruta accesible públicamente
		imageOverlayPath = `/uploads/${imageOverlay.name}`;
	}

	// Guardar en SQLite
	const card = cardsDB.createCard({
		created_at,
		code,
		name,
		is_evolution,
		next_evolution,
		description,
		image: imagePath ?? '',
		overlay_image: imageOverlayPath ?? '',
		first_element,
		second_element,
		type,
		character,
		first_attack,
		second_attack,
		health,
		physical_defence,
		magic_defence,
		forces,
		ability,
		association
	});

	return json({ card }, { status: 201 });
}


// DELETE
export async function DELETE({ request }) {
	const { id } = await request.json();
	if (!id) {
		return json({ error: 'Missing id' }, { status: 400 });
	}

	const success = cardsDB.deleteCard(Number(id));
	if (!success) {
		return json({ error: 'Card not found' }, { status: 404 });
	}

	return json({ success: true });
}