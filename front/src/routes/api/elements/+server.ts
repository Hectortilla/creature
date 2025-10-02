import { json } from '@sveltejs/kit';
import * as typesDB from '$lib/server/types/database.js';

export async function GET() {
	return json({ types: typesDB.getAllTypes() });
}
