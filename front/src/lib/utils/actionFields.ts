/**
 * Action field mappings
 *
 * Fully dynamically derived from the generated OpenAPI client SDK.
 * Field metadata is auto-generated from types.gen.ts by scripts/generate-action-metadata.ts
 *
 * To regenerate metadata after API changes:
 *   npm run generate-action-metadata
 *   or
 *   npm run generate (generates client + metadata)
 */

// Import auto-generated metadata (regenerate with: npm run generate-action-metadata)
import {
	FIELD_METADATA as GENERATED_FIELD_METADATA,
	NO_FIELD_ACTION_TYPES as GENERATED_NO_FIELD_ACTION_TYPES,
	ALL_ACTION_TYPES as GENERATED_ALL_ACTION_TYPES,
	type FieldMetadata,
} from "./generated/actionFields.metadata";

export interface ActionFieldConfig {
	name: string;
	label: string;
	type: "text" | "number" | "select" | "multiselect" | "json";
	required: boolean;
	description?: string;
	example?: string | number | string[];
	placeholder?: string;
}

export interface ActionTypeConfig {
	type: string;
	label: string;
	description: string;
	fields: ActionFieldConfig[];
}

/**
 * Special cases for field requirements per action type
 * Overrides the default isOptional behavior for specific action+field combinations
 */
const FIELD_REQUIREMENT_OVERRIDES: Record<string, Record<string, boolean>> = {
	attack: {
		target_card_id: false, // target_card_id is optional for attack
	},
};

/**
 * Convert TypeScript type to field input type
 */
function tsTypeToFieldType(
	tsType: string,
): "text" | "number" | "select" | "multiselect" | "json" {
	if (tsType.includes("Array")) {
		if (
			tsType.includes("swaps") ||
			tsType.includes("{") ||
			tsType.includes("unknown")
		) {
			return "json";
		}
		return "multiselect";
	}
	if (tsType === "number" || tsType.includes("number")) {
		return "number";
	}
	return "text";
}

/**
 * Generate human-readable label from action type
 */
function generateActionLabel(actionType: string): string {
	return actionType
		.split("_")
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(" ");
}

/**
 * Generate description from action type
 */
function generateActionDescription(actionType: string): string {
	const label = generateActionLabel(actionType);
	return `${label} action`;
}

/**
 * Generate label from field name
 */
function generateFieldLabel(fieldName: string): string {
	return fieldName
		.split("_")
		.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
		.join(" ");
}

/**
 * Generate placeholder from example
 */
function generatePlaceholder(
	example: string | number | string[] | undefined,
	_fieldName: string,
): string | undefined {
	if (example === undefined) {
		return undefined;
	}
	if (typeof example === "string") {
		return example;
	}
	if (typeof example === "number") {
		return example.toString();
	}
	if (Array.isArray(example)) {
		if (example.length > 0 && typeof example[0] === "string") {
			return example.join(", ");
		}
		return JSON.stringify(example);
	}
	return undefined;
}

/**
 * Build field config from metadata
 */
function buildFieldConfig(
	metadata: FieldMetadata,
	actionType: string,
): ActionFieldConfig {
	const fieldType = tsTypeToFieldType(metadata.tsType);

	// Check for requirement overrides first
	const override = FIELD_REQUIREMENT_OVERRIDES[actionType]?.[metadata.name];
	const isRequired = override !== undefined ? override : !metadata.isOptional; // Required if not optional

	return {
		name: metadata.name,
		label: generateFieldLabel(metadata.name),
		type: fieldType,
		required: isRequired,
		description: metadata.description,
		placeholder: generatePlaceholder(undefined, metadata.name), // Examples not in metadata yet
	};
}

/**
 * Get fields for a specific action type
 */
function getFieldsForActionType(actionType: string): ActionFieldConfig[] {
	const fields: ActionFieldConfig[] = [];

	// Find all fields used by this action type
	for (const fieldMeta of GENERATED_FIELD_METADATA) {
		if (fieldMeta.usedBy.includes(actionType)) {
			const fieldConfig = buildFieldConfig(fieldMeta, actionType);
			fields.push(fieldConfig);
		}
	}

	return fields;
}

/**
 * Build action type config dynamically
 */
function buildActionTypeConfig(actionType: string): ActionTypeConfig {
	return {
		type: actionType,
		label: generateActionLabel(actionType),
		description: generateActionDescription(actionType),
		fields: getFieldsForActionType(actionType),
	};
}

/**
 * Dynamically generated action type configurations
 * All action types are inferred from auto-generated FIELD_METADATA
 */
export const ACTION_TYPE_CONFIGS: Record<string, ActionTypeConfig> =
	Object.fromEntries(
		GENERATED_ALL_ACTION_TYPES.map((actionType) => [
			actionType,
			buildActionTypeConfig(actionType),
		]),
	);

// Add no-field action types
for (const actionType of GENERATED_NO_FIELD_ACTION_TYPES) {
	if (!ACTION_TYPE_CONFIGS[actionType]) {
		ACTION_TYPE_CONFIGS[actionType] = buildActionTypeConfig(actionType);
	}
}

/**
 * Get all known action types
 */
export function getAllActionTypes(): string[] {
	return Object.keys(ACTION_TYPE_CONFIGS).sort();
}

/**
 * Get configuration for a specific action type
 */
export function getActionConfig(
	actionType: string,
): ActionTypeConfig | undefined {
	return ACTION_TYPE_CONFIGS[actionType];
}

/**
 * Get fields for a specific action type
 */
export function getActionFields(actionType: string): ActionFieldConfig[] {
	return ACTION_TYPE_CONFIGS[actionType]?.fields ?? [];
}
