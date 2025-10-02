import { json } from '@sveltejs/kit';
import * as charactersDB from '$lib/server/characters/database.js';

export async function GET() {
	return json({ characters: charactersDB.getAllCharacters() });
}
