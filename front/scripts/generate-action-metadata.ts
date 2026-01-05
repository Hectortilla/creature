/**
 * Build script to generate action field metadata from generated API types
 * This script parses types.gen.ts and generates actionFields.metadata.ts
 * 
 * Run this after generating the API client: npm run generate-client
 */

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface ParsedFieldMetadata {
	name: string;
	tsType: string;
	description: string;
	usedBy: string[];
	isOptional: boolean;
}

/**
 * Parse the ActionData type definition from the generated types file
 */
function parseActionDataFromTypes(): ParsedFieldMetadata[] {
	const typesPath = join(__dirname, '../src/lib/api/types.gen.ts');
	const content = readFileSync(typesPath, 'utf-8');
	
	// Find the ActionData type definition
	const actionDataStart = content.indexOf('export type ActionData = {');
	if (actionDataStart === -1) {
		throw new Error('ActionData type not found in types.gen.ts');
	}
	
	// Find the end of the ActionData type (next export or closing brace)
	let braceCount = 0;
	let inType = false;
	let typeContent = '';
	
	for (let i = actionDataStart; i < content.length; i++) {
		const char = content[i];
		if (char === '{') {
			braceCount++;
			inType = true;
		} else if (char === '}') {
			braceCount--;
			if (braceCount === 0 && inType) {
				typeContent = content.substring(actionDataStart, i + 1);
				break;
			}
		}
	}
	
	// Parse fields from the type content using regex
	const fields: ParsedFieldMetadata[] = [];
	
	// Match JSDoc comments followed by field definitions
	// Pattern: /** ... */ fieldName?: type;
	// Handle multi-line types by matching until semicolon
	const fieldPattern = /\/\*\*([\s\S]*?)\*\/\s*(\w+)(\??):\s*([^;]+);/g;
	let match;
	
	while ((match = fieldPattern.exec(typeContent)) !== null) {
		const [, jsdoc, fieldName, optional, tsTypeRaw] = match;
		
		// Skip action_type field
		if (fieldName === 'action_type') {
			continue;
		}
		
		// Parse description from JSDoc - extract the main description line
		const descriptionLines = jsdoc
			.split('\n')
			.map(l => l.replace(/^\s*\*\s?/, '').trim())
			.filter(l => l && !l.startsWith('/') && !l.startsWith('*') && l.length > 0);
		
		// Get the main description (usually the first non-empty line after the field name)
		// Format is usually: "* Field Name\n*\n* Description text"
		let mainDescription = '';
		for (let i = 0; i < descriptionLines.length; i++) {
			const line = descriptionLines[i];
			// Skip lines that are just field names or empty
			if (line && !line.match(/^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$/)) {
				mainDescription = line;
				break;
			}
		}
		
		// If no main description found, use the first meaningful line
		if (!mainDescription && descriptionLines.length > 0) {
			mainDescription = descriptionLines.find(l => l && !l.match(/^[A-Z]/)) || descriptionLines[0] || '';
		}
		
		// Extract "used by" information from all description lines
		const fullDescription = descriptionLines.join(' ');
		const usedByMatch = fullDescription.match(/used by:\s*([^.)]+)/i);
		const usedBy = usedByMatch
			? usedByMatch[1]
				.split(',')
				.map(s => s.trim())
				.filter(s => s.length > 0)
			: [];
		
		// Clean up description (remove "used by" part and field name if duplicated)
		let cleanDescription = mainDescription
			.replace(/\s*\(used by:.*?\)/i, '')
			.replace(/\s*used by:.*?$/i, '')
			.replace(/\s*used by:.*?\./i, '')
			.trim();
		
		// Remove field name if it appears at the start of description
		const fieldNameWords = fieldName.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1));
		const fieldNamePattern = new RegExp(`^${fieldNameWords.join('\\s+')}\\s+`, 'i');
		cleanDescription = cleanDescription.replace(fieldNamePattern, '').trim();
		
		// Fix tsType - handle multi-line array types
		let tsType = tsTypeRaw.trim();
		// If type is incomplete (ends with newline or {), find the complete type
		if (tsType.includes('\n') || tsType.endsWith('{')) {
			// Find the complete type by looking for the closing brace and semicolon
			const typeStart = match.index! + match[0].indexOf(tsTypeRaw);
			let typeEnd = typeStart + tsTypeRaw.length;
			let braceCount = (tsType.match(/{/g) || []).length - (tsType.match(/}/g) || []).length;
			
			while (braceCount > 0 && typeEnd < content.length) {
				const char = content[typeEnd];
				if (char === '{') braceCount++;
				if (char === '}') braceCount--;
				typeEnd++;
			}
			
			// Find the semicolon
			while (typeEnd < content.length && content[typeEnd] !== ';') {
				typeEnd++;
			}
			
			tsType = content.substring(typeStart, typeEnd).trim();
		}
		
		fields.push({
			name: fieldName,
			tsType: tsType,
			description: cleanDescription || mainDescription || fullDescription,
			usedBy,
			isOptional: optional === '?'
		});
	}
	
	return fields;
}

/**
 * Generate the metadata file
 */
async function generateMetadataFile() {
	try {
		const fields = parseActionDataFromTypes();
		
		// Read the types file again to extract action type examples
		const typesPath = join(__dirname, '../src/lib/api/types.gen.ts');
		const content = readFileSync(typesPath, 'utf-8');
		
		// Extract all unique action types from fields
		const actionTypes = new Set<string>();
		fields.forEach(field => {
			field.usedBy.forEach(actionType => actionTypes.add(actionType));
		});
		
		// Also try to extract action types from OpenAPI JSON
		// The examples are in the OpenAPI schema, not the generated TypeScript
		try {
			const apiUrl = process.env.PUBLIC_API_URL || 'http://localhost:8000';
			const openApiUrl = `${apiUrl}/openapi.json`;
			
			// Try to fetch from URL first (if server is running)
			let openApiContent: string;
			try {
				const response = await fetch(openApiUrl);
				if (response.ok) {
					openApiContent = await response.text();
				} else {
					throw new Error('Failed to fetch OpenAPI JSON');
				}
			} catch {
				// If fetch fails, try to read from a local file if it exists
				// This is a fallback - the user should run the server or have the file
				console.warn(`⚠️  Could not fetch OpenAPI from ${openApiUrl}`);
				console.warn('   Action types "pass" and "concede" may be missing.');
				console.warn('   Make sure the backend server is running or update NO_FIELD_ACTION_TYPES manually.');
			}
			
			if (openApiContent) {
				const openApi = JSON.parse(openApiContent);
				// Navigate to ActionData.action_type.examples
				const actionDataSchema = openApi?.components?.schemas?.ActionData;
				if (actionDataSchema?.properties?.action_type?.examples) {
					const examples = actionDataSchema.properties.action_type.examples;
					if (Array.isArray(examples)) {
						examples.forEach((actionType: string) => actionTypes.add(actionType));
					}
				}
			}
		} catch (error) {
			// Silently fail - we'll use what we found from fields
			console.warn('Could not parse OpenAPI JSON for action type examples:', error);
		}
		
		// Generate the metadata file content
		const metadataContent = `/**
 * Auto-generated action field metadata
 * 
 * This file is automatically generated by scripts/generate-action-metadata.ts
 * Do not edit manually. Run 'npm run generate-action-metadata' to regenerate.
 * 
 * Generated from: src/lib/api/types.gen.ts
 */

export interface FieldMetadata {
	name: string;
	tsType: string;
	description: string;
	usedBy: string[];
	isOptional: boolean;
}

export const FIELD_METADATA: FieldMetadata[] = ${JSON.stringify(fields, null, '\t')};

/**
 * Action types that don't use any fields (no-parameter actions)
 */
export const NO_FIELD_ACTION_TYPES: string[] = ${JSON.stringify(
			Array.from(actionTypes).filter(
				actionType => !fields.some(f => f.usedBy.includes(actionType))
			),
			null,
			'\t'
		)};

/**
 * All discovered action types
 */
export const ALL_ACTION_TYPES: string[] = ${JSON.stringify(
			Array.from(actionTypes).sort(),
			null,
			'\t'
		)};
`;

		const outputPath = join(__dirname, '../src/lib/utils/actionFields.metadata.ts');
		writeFileSync(outputPath, metadataContent, 'utf-8');
		
		console.log('✅ Generated action field metadata successfully!');
		console.log(`   Found ${fields.length} fields`);
		console.log(`   Found ${actionTypes.size} action types`);
	} catch (error) {
		console.error('❌ Error generating action field metadata:', error);
		process.exit(1);
	}
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
	generateMetadataFile().catch(error => {
		console.error('Error:', error);
		process.exit(1);
	});
}

export { generateMetadataFile };

