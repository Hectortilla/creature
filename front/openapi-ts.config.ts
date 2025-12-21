/// <reference types="node" />
import { defineConfig } from '@hey-api/openapi-ts';
import 'dotenv/config';

const apiUrl = process.env.PUBLIC_API_URL || 'http://localhost:8000';

export default defineConfig({
	client: '@hey-api/client-fetch',
	input: `${apiUrl}/openapi.json`,
	output: {
		path: 'src/lib/api',
		format: 'prettier',
	},
});
