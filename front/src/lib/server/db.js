import Database from 'better-sqlite3';

const db = new Database('database.db');

// Tabla de cartas
db.prepare(`
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        code INTEGER UNIQUE,
        is_evolution INTEGER NOT NULL DEFAULT 0,
        name TEXT NOT NULL,
        handle TEXT NOT NULL,
        description TEXT,
        image TEXT,
        firstElement TEXT,
        secondElement TEXT,
        type TEXT,
        character TEXT,
        health INTEGER,
        physical_defence INTEGER,
        magic_defence INTEGER
    )
`).run();

// Tabla de elementos
db.prepare(`
    CREATE TABLE IF NOT EXISTS elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        strengths TEXT,
        weaknesses TEXT
    )
`).run();

// Tabla de ataques
db.prepare(`
    CREATE TABLE IF NOT EXISTS attacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code INTEGER UNIQUE,
        name TEXT NOT NULL
    )
`).run();

// Tabla de habilidades
db.prepare(`
    CREATE TABLE IF NOT EXISTS abilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code INTEGER UNIQUE,
        name TEXT NOT NULL
    )
`).run();

// mejora la concurrencia
db.pragma("journal_mode = WAL");

export default db;