PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
  );
INSERT INTO elements VALUES(1,'Ether');
INSERT INTO elements VALUES(2,'Aire');
CREATE TABLE attacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    power INTEGER
  );
INSERT INTO attacks VALUES(1,'Arañazo',40);
CREATE TABLE IF NOT EXISTS "cards" (
	"id"	INTEGER,
	"code"	INTEGER,
	"name"	TEXT NOT NULL,
	"elements"	TEXT,
	"handle"	TEXT NOT NULL,
	"description"	TEXT,
	"image"	BLOB,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO cards VALUES(1,1,'Dragón','','dragon','Dragón descripción','/images/cards/dragon.jpg');
INSERT INTO cards VALUES(2,2,'Bruja',NULL,'bruja','Bruja descripción','/images/cards/bruja.jpg');
INSERT INTO cards VALUES(4,3,'Test 1',NULL,'test-1','description',NULL);
INSERT INTO cards VALUES(5,4,'Test 1',NULL,'test-1','test',NULL);
INSERT INTO cards VALUES(6,5,'aa aa',NULL,'aa-aa','aaaa',NULL);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('elements',2);
INSERT INTO sqlite_sequence VALUES('attacks',1);
INSERT INTO sqlite_sequence VALUES('cards',6);
COMMIT;
