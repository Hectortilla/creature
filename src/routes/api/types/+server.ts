import { json } from '@sveltejs/kit';
import * as elementsDB from '$lib/server/elements/database.js';

export async function GET() {
	return json({ elements: elementsDB.getAllElements() });
}
