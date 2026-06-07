"""Initial schema and data

Revision ID: 001
Revises:
Create Date: 2025-12-20

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create tables

    # Elements table
    op.create_table(
        "elements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("strengths", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("weaknesses", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )

    # Types table
    op.create_table(
        "types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )

    # Characters table
    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("icon", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("label"),
    )

    # Abilities table
    op.create_table(
        "abilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Associations table
    op.create_table(
        "associations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Attacks table (depends on elements)
    op.create_table(
        "attacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("damage", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("dice_rolls", sa.Integer(), nullable=True),
        sa.Column("necessary_force", postgresql.JSONB(), nullable=True),
        sa.Column("effect", sa.Text(), nullable=True),
        sa.Column("element_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["element_id"],
            ["elements.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Cards table (depends on many tables)
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("code", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("handle", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("overlay_image", sa.String(length=500), nullable=True),
        sa.Column("health", sa.Integer(), nullable=True),
        sa.Column("physical_defence", sa.Integer(), nullable=True),
        sa.Column("magic_defence", sa.Integer(), nullable=True),
        sa.Column("forces", postgresql.JSONB(), nullable=True),
        sa.Column("is_evolution_id", sa.Integer(), nullable=True),
        sa.Column("first_element_id", sa.Integer(), nullable=True),
        sa.Column("second_element_id", sa.Integer(), nullable=True),
        sa.Column("type_id", sa.Integer(), nullable=True),
        sa.Column("character_id", sa.Integer(), nullable=True),
        sa.Column("first_attack_id", sa.Integer(), nullable=True),
        sa.Column("second_attack_id", sa.Integer(), nullable=True),
        sa.Column("ability_id", sa.Integer(), nullable=True),
        sa.Column("association_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["is_evolution_id"],
            ["cards.id"],
        ),
        sa.ForeignKeyConstraint(
            ["first_element_id"],
            ["elements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["second_element_id"],
            ["elements.id"],
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["types.id"],
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["characters.id"],
        ),
        sa.ForeignKeyConstraint(
            ["first_attack_id"],
            ["attacks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["second_attack_id"],
            ["attacks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["ability_id"],
            ["abilities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["association_id"],
            ["associations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Insert initial data
    # Note: Using exec_driver_sql() to prevent SQLAlchemy from interpreting colons in JSON as bind parameters
    conn = op.get_bind()

    # Elements data
    conn.exec_driver_sql("""
        INSERT INTO elements (id, label, icon, color, strengths, weaknesses) VALUES
        (1, 'Ether', '/images/elements/ether.png', 'BCBCBC', '{11}', '{12}'),
        (2, 'Tierra', '/images/elements/ground.png', '5D371A', '{7,8}', '{3,9}'),
        (3, 'Agua', '/images/elements/water.png', '3E82B6', '{2,5}', '{7,9}'),
        (4, 'Aire', '/images/elements/air.png', '7FB9DA', '{5,9}', '{2,7}'),
        (5, 'Fuego', '/images/elements/fire.png', 'CB4634', '{6,9}', '{3,4}'),
        (6, 'Hielo', '/images/elements/ice.png', '70D4DA', '{4,9}', '{5,8}'),
        (7, 'Rayo', '/images/elements/thunder.png', 'CBB734', '{3,6}', '{2,8}'),
        (8, 'Metal', '/images/elements/metal.png', '939393', '{6,11}', '{2,9}'),
        (9, 'Flora', '/images/elements/nature.png', '48A819', '{8,12}', '{5,6}'),
        (10, 'Tóxico', '/images/elements/toxic.png', '891CBF', '{9,10}', '{2,11}'),
        (11, 'Mental', '/images/elements/mental.png', 'D92FC5', '{10,11}', '{13,11}'),
        (12, 'Luz', '/images/elements/light.png', 'E8E7D7', '{1}', '{13,9}'),
        (13, 'Oscuridad', '/images/elements/darkness.png', '2D2733', '{12}', '{1,8}');
    """)

    # Update sequence for elements
    conn.exec_driver_sql("SELECT setval('elements_id_seq', (SELECT MAX(id) FROM elements));")

    # Types data
    conn.exec_driver_sql("""
        INSERT INTO types (id, label, icon) VALUES
        (1, 'Primordial', 'primordial'),
        (2, 'Guerrero', 'warrior'),
        (3, 'Hechicero', 'wizard'),
        (4, 'Criatura', 'creature'),
        (5, 'Arma', 'weapon'),
        (6, 'Objeto', 'object'),
        (7, 'Campo', 'field');
    """)

    # Update sequence for types
    conn.exec_driver_sql("SELECT setval('types_id_seq', (SELECT MAX(id) FROM types));")

    # Characters data
    conn.exec_driver_sql("""
        INSERT INTO characters (id, label, icon) VALUES
        (1, 'Ancestral', 'ancestral'),
        (2, 'Elemental', 'elemental'),
        (3, 'Leyenda', 'leyend'),
        (4, 'Heroe', 'hero'),
        (5, 'Mágico', 'magic'),
        (6, 'No muerto', 'undead'),
        (7, 'Común', 'common');
    """)

    # Update sequence for characters
    conn.exec_driver_sql("SELECT setval('characters_id_seq', (SELECT MAX(id) FROM characters));")

    # Abilities data
    conn.exec_driver_sql("""
        INSERT INTO abilities (id, code, handle, name, description, created_at, type) VALUES
        (1, 1, 'sequedad', 'Sequedad', 'Los ataques de tipo <water> le hacen +10 de daño independientemente del tipo de la carta.
Los ataque de tipo <ground> le hacen -10 de daño independientemente del tipo de la carta.', '2025-09-03T12:41:17.295Z', 'magical'),
        (3, 2, 'esqueje', 'Esqueje', 'Aporta +10 <health> y +10 puntos de ataque a cartas <nature>', '2025-09-21T08:13:39.164Z', 'physical'),
        (4, 3, 'paz-mental', 'Paz mental', 'A las cartas <mental> no les afectan las habilidades negativas <magical>.', '2025-09-21T08:16:50.655Z', 'magical'),
        (5, 4, 'proteico', 'Proteico', 'Aumenta el ataque <physical> en +10 puntos de daño de tus cartas.', '2025-09-21T08:35:32.663Z', 'physical'),
        (6, 5, 'contemporizar', 'Contemporizar', 'Si esta carta se encuentra en la zona de segunda línea, cuando una carta aliada ataque, también atacará a la carta rival infligiendo <n>1/3</n> de su primer ataque.', '2025-09-21T08:44:35.583Z', 'physical'),
        (7, 6, 'escudo', 'Escudo', 'Aumenta la defensa <physical> en +10 puntos de tus cartas.', '2025-09-21T09:30:33.610Z', 'physical'),
        (8, 7, 'sacrificio', 'Sacrificio', 'Esta carta puede ser intercambiada por una carta aliada del cementerio al final del turno.', '2025-09-21T09:32:13.697Z', 'magical'),
        (9, 8, 'control-total-sobre-la-magia', 'Control total sobre la mágia', 'No le afectan ataques ni habilidades <magical> rivales.', '2025-09-21T09:33:41.109Z', 'magical'),
        (10, 9, 'individualista', 'Individualista', 'No es posible usar asociaciones con esta carta.', '2025-09-21T09:34:47.418Z', 'physical'),
        (11, 10, 'trabajo-en-equipo', 'Trabajo en equipo', 'Esta carta puede asumir hasta <n>2</n> cartas asociadas.', '2025-09-21T09:35:33.226Z', 'physical'),
        (12, 11, 'piel-ardiente', 'Piel ardiente', 'Al recibir un ataque, la carta rival que no sea <fire>, recibe -10 <health>', '2025-09-21T09:36:34.096Z', 'physical'),
        (13, 12, 'bajo-cero', 'Bajo cero', 'Al recibir un ataque, la carta rival que no sea <ice>, no podrá atacar en el siguiente turno por congelación.', '2025-09-21T09:37:58.390Z', 'physical'),
        (14, 13, 'estatica', 'Estática', 'Al recibir un ataque, la carta rival que no sea <thunder> o <ground>, no podrá atacar en el siguiente turno por estar paralizado.', '2025-09-21T09:39:32.701Z', 'physical'),
        (15, 14, 'intangible', 'Intangible', 'No le afectan ataques ni habilidades <physical> rivales.', '2025-09-21T11:27:58.436Z', 'magical'),
        (16, 15, 'luna-de-sangre', 'Luna de sangre', 'Cada <n>3</n> turnos los puntos de ataque <physical> y <magical> se multiplican <n>x2</n>.', '2025-09-21T11:30:53.955Z', 'magical'),
        (17, 16, 'hijas-de-nix', 'Hijas de Nix', 'Aumenta la defensa <magical> en +20 puntos por cada carta <i>Moira</i> en juego.', '2025-09-21T11:38:29.634Z', 'magical'),
        (18, 17, 'nevada', 'Nevada', 'Aumenta el ataque <physical> y <magical> de cartas <ice> en +20 puntos.', '2025-09-21T14:52:28.501Z', 'physical'),
        (19, 18, 'sofoco', 'Sofoco', 'Aumenta los ataques <physical> y <magical> de las cartas <fire> en +20 puntos.', '2025-09-21T14:56:23.335Z', 'physical');
    """)

    # Update sequence for abilities
    conn.exec_driver_sql("SELECT setval('abilities_id_seq', (SELECT MAX(id) FROM abilities));")

    # Associations data
    conn.exec_driver_sql("""
        INSERT INTO associations (id, code, name, handle, description, created_at) VALUES
        (1, 1, 'Buena suerte', 'buena-suerte', 'Se asocia a cartas de naturaleza <undead> aportando +20 en defensa <magical>', '2025-09-03T12:41:17.295Z'),
        (5, 2, 'Cambio de guardia', 'cambio-de-guardia', 'Cuando esta carta se asocia a otra en la zona de ataque, puede intercambiarse por otra en la zona de segunda línea sin coste de cambio. Una vez hecho el cambio esta carta se elimina de la partida (no va al cementerio). Puede ser jugada desde la mano directamente.', '2025-09-21T08:22:13.491Z'),
        (6, 3, 'Brote', 'brote', 'Aumenta el ataque y la vida <health> de una carta <nature> en +20 puntos.', '2025-09-21T08:23:46.561Z'),
        (7, 4, 'Maldición del alma perdida', 'maldicion-del-alma-perdida', 'Reduce las defensas <physical> y <magical> de la carta a 0. Cada turno, un turno después de ser asociada, reduce -10 los puntos de vida de la carta. Aumenta su ataque en +40.', '2025-09-21T08:27:54.542Z'),
        (8, 5, 'Proteina', 'proteina', 'Aumenta el ataque <physical> en +20 puntos de daño.', '2025-09-21T08:35:10.808Z'),
        (9, 6, 'Mutación X', 'mutacion-x', 'Aumenta el ataque <physical> y <magical> en +20 puntos de daño de cartas <creature>', '2025-09-21T08:37:33.175Z'),
        (10, 7, 'Poción', 'pocion', 'Aumenta los puntos de <health> en +20. La carta debe ser enviada al cementerio una vez usada.', '2025-09-21T09:47:26.801Z');
    """)

    # Update sequence for associations
    conn.exec_driver_sql("SELECT setval('associations_id_seq', (SELECT MAX(id) FROM associations));")

    # Attacks data
    conn.exec_driver_sql("""
        INSERT INTO attacks (id, code, created_at, name, handle, damage, type, element_id, dice_rolls, necessary_force, description, effect) VALUES
        (13, 3, '2025-09-17T16:31:32.776Z', 'Chispa colateral', 'chispa-colateral', 10, 'physical', 7, 2, '[{"value":2,"elementData":{"id":8,"label":"Rayo","color":"CBB734","icon":"/images/elements/thunder.png"}}]', 'Chíspas eléctricas que rebotan en la carta atacada haciendo un daño colateral.', 'Hace la mitad del daño del ataque a una carta inmediatamente al lado en el tapiz a la carta atacada. Si hay dos cartas rivales que pueden recibir este daño, el atacante decide cual de ellas lo recibe. Si la carta atacada es de elemento <thunder> no tendrá efecto.'),
        (14, 1, '2025-09-20T17:16:31.607Z', 'Empujón', 'empujon', 50, 'physical', 1, 0, '[{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Usa su propio cuerpo para empujar al rival.', NULL),
        (15, 2, '2025-09-20T17:31:10.606Z', 'Agarre', 'agarre', 50, 'physical', 1, 0, '[{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Agarra, zarandea y empuja al rival con todo su cuerpo.', 'Tira un <dice>, si sale <n>3</n> la carta atacada necesitará sacar un <n>3</n><dice> en su próximo turno para poder atacar.'),
        (16, 4, '2025-09-20T19:11:57.891Z', 'Eco', 'eco', 10, 'physical', 1, 3, '[{"value":2,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Emite un sonido de alta frecuencia que hiere a las dos cartas de la zona de ataque rival.', 'Afecta a ambas cartas en la zona de ataque rival.'),
        (17, 5, '2025-09-20T20:03:06.981Z', 'Runa', 'runa', 60, 'magical', 2, 0, '[{"value":1,"elementData":{"id":2,"label":"Tierra","color":"5D371A","icon":"/images/elements/ground.png"}}]', 'Runas de piedra rodean al rival y terminan por golpearlo en secuencia.', NULL),
        (19, 6, '2025-09-20T20:09:30.274Z', 'Torrente', 'torrente', 60, 'physical', 3, 0, '[{"value":1,"elementData":{"id":3,"label":"Agua","color":"3E82B6","icon":"/images/elements/water.png"}}]', 'Reúne el agua del lugar y conduce hasta el rival golpeándolo con fuerza.', NULL),
        (20, 7, '2025-09-20T20:17:10.878Z', 'Brasas', 'brasas', 50, 'magical', 5, 0, '[{"value":1,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}},{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Invoca brasas justo debajo del rival que duran <n>2</n> turnos.', 'Durante los <n>2</n> próximos turnos el rival sufre -10 <health> cada turno. Este efecto no afecta a cartas <fire>'),
        (21, 8, '2025-09-20T20:23:45.468Z', 'Escarcha', 'escarcha', 50, 'magical', 6, 0, '[{"value":2,"elementData":{"id":6,"label":"Hielo","color":"70D4DA","icon":"/images/elements/ice.png"}}]', 'El rival sufre una congelación espontánea.', 'Durante los <n>2</n> próximos turnos el rival sufre -10 <health> cada turno. Este efecto no afecta a cartas <ice>'),
        (22, 9, '2025-09-20T20:26:22.417Z', 'Borrasca', 'borrasca', 10, 'physical', 4, 3, '[{"value":2,"elementData":{"id":4,"label":"Aire","color":"7FB9DA","icon":"/images/elements/air.png"}}]', 'Vientos rápidos golpean al rival.', NULL),
        (24, 11, '2025-09-20T20:34:03.885Z', 'Absorber energía', 'absorber-energia', 30, 'magical', 9, 0, '[{"value":1,"elementData":{"id":9,"label":"Flora","color":"48A819","icon":"/images/elements/nature.png"}}]', 'Absorbe la energía del rival para vitalizarse.', 'Recupera +10 <health>. Si el rival es <water> o <light> recupera +20 <health>.'),
        (25, 12, '2025-09-20T20:48:34.230Z', 'Canalizar', 'canalizar', 80, 'magical', 12, 0, '[{"value":2,"elementData":{"id":12,"label":"Luz","color":"E8E7D7","icon":"/images/elements/light.png"}},{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Recoge la luz de la estrella más cercana para usarla como arma.', NULL),
        (26, 13, '2025-09-20T20:53:29.231Z', 'Jaqueca', 'jaqueca', 60, 'magical', 11, 0, '[{"value":1,"elementData":{"id":11,"label":"Mental","color":"D92FC5","icon":"/images/elements/mental.png"}}]', 'El rival sufre un dolor intenso y repentino.', NULL),
        (27, 14, '2025-09-21T08:47:23.353Z', 'Filo', 'filo', 50, 'physical', 8, 0, '[{"value":2,"elementData":{"id":8,"label":"Metal","color":"939393","icon":"/images/elements/metal.png"}}]', 'Golpea con una parte afilada de su cuerpo.', NULL),
        (28, 15, '2025-09-21T08:52:45.204Z', 'Martillazo', 'martillazo', 80, 'physical', 8, 0, '[{"value":2,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}},{"value":1,"elementData":{"id":8,"label":"Metal","color":"939393","icon":"/images/elements/metal.png"}}]', 'Golpea duro levantando el puño como un martillo y aprovechando la gravedad en el golpe.', NULL),
        (29, 16, '2025-09-21T08:55:14.363Z', 'Fuegos fatuos', 'fuegos-fatuos', 10, 'magical', 5, 3, '[{"value":1,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}},{"value":1,"elementData":{"id":13,"label":"Oscuridad","color":"2D2733","icon":"/images/elements/darkness.png"}}]', 'Pequeños fuegos pálidos que atacan  y queman al rival.', NULL),
        (30, 17, '2025-09-21T08:57:59.795Z', 'Explosión eléctrica', 'explosion-electrica', 70, 'physical', 7, 0, '[{"value":2,"elementData":{"id":7,"label":"Rayo","color":"CBB734","icon":"/images/elements/thunder.png"}},{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Pequeña explosión eléctrica dirigida hacia el rival.', 'Tira un <dice>, si el resultado es <n>3</n>, la carta del rival no podrá atacar el próximo turno.'),
        (31, 18, '2025-09-21T09:00:37.706Z', 'Derrumbamiento', 'derrumbamiento', 90, 'physical', 2, 0, '[{"value":3,"elementData":{"id":2,"label":"Tierra","color":"5D371A","icon":"/images/elements/ground.png"}}]', 'Aprovecha el entorno para lanzar un trozo de terreno encima del rival.', NULL),
        (32, 19, '2025-09-21T09:02:39.885Z', 'Deshumidificar', 'deshumidificar', 90, 'magical', 3, 0, '[{"value":3,"elementData":{"id":3,"label":"Agua","color":"3E82B6","icon":"/images/elements/water.png"}}]', 'El rival empieza secarse de dentro a fuera. ', NULL),
        (33, 20, '2025-09-21T09:08:51.728Z', 'Vendaval ', 'vendaval-', 20, 'physical', 4, 2, '[{"value":2,"elementData":{"id":4,"label":"Aire","color":"7FB9DA","icon":"/images/elements/air.png"}},{"value":2,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'Viento fuerte que golpea al rival en dos ocaciones.', 'Si el daño infligido supera los +100 puntos, el rival debe intercambiar la carta afectada por otra de la zona de segunda línea sin coste de cambio. Si no hay cartas en la segunda línea, o la carta rival queda con 0 puntos de vida, este efecto no se aplica.'),
        (34, 21, '2025-09-21T09:12:04.095Z', 'Hoja daga', 'hoja-daga', 60, 'physical', 9, 0, '[{"value":2,"elementData":{"id":9,"label":"Flora","color":"48A819","icon":"/images/elements/nature.png"}}]', 'Usa las hojas del entorno como dagas contra el rival.', NULL),
        (35, 22, '2025-09-21T09:14:44.028Z', 'Bola de nieve', 'bola-de-nieve', 80, 'physical', 6, 0, '[{"value":2,"elementData":{"id":6,"label":"Hielo","color":"70D4DA","icon":"/images/elements/ice.png"}}]', 'Se va formando una bola de nieve que ataca al rival en el siguiente turno.', 'Este ataque necesita un turno de margen para atacar.'),
        (36, 23, '2025-09-21T09:17:45.669Z', 'Roce tóxico', 'roce-toxico', 30, 'physical', 10, 0, '[{"value":1,"elementData":{"id":10,"label":"Tóxico","color":"891CBF","icon":"/images/elements/toxic.png"}},{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'El propio roce de la piel con el rival genera un sarpullido.', 'Durante los dos turnos siguientes, el rival recibe -10 puntos de daño por cada turno. No tiene efecto contra cartas <toxic>'),
        (37, 24, '2025-09-21T09:19:30.856Z', 'Vómito', 'vomito', 60, 'physical', 10, 0, '[{"value":1,"elementData":{"id":10,"label":"Tóxico","color":"891CBF","icon":"/images/elements/toxic.png"}}]', 'Usa su propia bilis para generar un vómito corrosivo que daña al rival.', 'Se hace -10 puntos de daño a sí mismo.'),
        (38, 25, '2025-09-21T09:21:05.520Z', 'Estrés', 'estres', 100, 'physical', 11, 0, '[{"value":3,"elementData":{"id":11,"label":"Mental","color":"D92FC5","icon":"/images/elements/mental.png"}}]', 'Modifica la mente del rival para generar un estrés tan fuerte que le genera un daño físico.', NULL),
        (39, 26, '2025-09-21T09:23:26.820Z', 'Algo divino', 'algo-divino', 120, 'magical', 12, 0, '[{"value":3,"elementData":{"id":12,"label":"Luz","color":"E8E7D7","icon":"/images/elements/light.png"}},{"value":2,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 'No se tiene mucha información sobre como actúa este ataque.', NULL),
        (40, 27, '2025-09-21T09:24:48.732Z', 'Congoja', 'congoja', 40, 'magical', 13, 0, '[{"value":2,"elementData":{"id":13,"label":"Oscuridad","color":"2D2733","icon":"/images/elements/darkness.png"}}]', 'Usa el miedo para generar un daño al rival.', NULL),
        (41, 28, '2025-09-21T09:29:26.590Z', 'Invocación', 'invocacion', 90, 'magical', 13, 0, '[{"value":3,"elementData":{"id":13,"label":"Oscuridad","color":"2D2733","icon":"/images/elements/darkness.png"}}]', 'Es capaz de invocar espíritus del cementerio de cartas para atacar a su rival.', 'Este ataque solo puede usarse si en el cementerio hay cartas aliadas que no sean <darkness>. La carta aliada seleccionada se elimina del juego después de ser utilizada.');
    """)

    # Update sequence for attacks
    conn.exec_driver_sql("SELECT setval('attacks_id_seq', (SELECT MAX(id) FROM attacks));")

    # Cards data - Note: The JSON stores attack/ability/association by CODE, not ID.
    # We need to map codes to actual IDs:
    #
    # Attack code -> ID: 1->14, 2->15, 3->13, 4->16, 5->17, 6->19, 7->20, 8->21, 9->22,
    #                   11->24, 12->25, 13->26, 14->27, 15->28, 16->29, 17->30, 18->31,
    #                   19->32, 20->33, 21->34, 22->35, 23->36, 24->37, 25->38, 26->39,
    #                   27->40, 28->41
    #
    # Ability code -> ID: 1->1, 2->3, 3->4, 4->5, 5->6, 6->7, 7->8, 8->9, 9->10, 10->11,
    #                    11->12, 12->13, 13->14, 14->15, 15->16, 16->17, 17->18, 18->19
    #
    # Association code -> ID: 1->1, 2->5, 3->6, 4->7, 5->8, 6->9, 7->10
    #
    # Card code -> ID (for is_evolution): 12->13 (Héroe), 16->17 (Come metal)

    conn.exec_driver_sql("""
        INSERT INTO cards (id, code, name, created_at, is_evolution_id, handle, description, image, overlay_image, first_element_id, second_element_id, type_id, character_id, health, physical_defence, magic_defence, forces, first_attack_id, second_attack_id, ability_id, association_id) VALUES
        (1, 1, 'Zero', '2025-09-21T10:15:24.350Z', NULL, 'zero', 'Se dice que cuando no existía nada, esta criatura, pululaba aburrida por un plano existencial desconocido.', '/uploads/zero.jpg', '', 1, NULL, 1, 1, 320, 10, 10, '[{"value":4,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 16, 39, 6, NULL),
        (2, 2, 'El Urco', '2025-09-21T11:11:10.621Z', NULL, 'el-urco', 'Perro del tamaño de un buey que arrastrar unas cadenas ancladas al fondo del mar. Su presencia augura muerte.', '/uploads/el-urco.jpg', '', 3, NULL, 4, 3, 290, 0, 10, '[{"value":2,"elementData":{"id":3,"label":"Agua","color":"3E82B6","icon":"/images/elements/water.png"}}]', 19, NULL, NULL, NULL),
        (3, 3, 'Golem', '2025-09-21T11:12:58.424Z', NULL, 'golem', 'Criatura de piedra que suele anidar en planetas rocosos.', '/uploads/golem.jpg', '', 2, NULL, 4, 7, 340, 0, 0, '[{"value":1,"elementData":{"id":2,"label":"Tierra","color":"5D371A","icon":"/images/elements/ground.png"}}]', 17, NULL, NULL, NULL),
        (4, 4, 'Hada del bosque', '2025-09-21T11:14:42.285Z', NULL, 'hada-del-bosque', '', '/uploads/hada-del-bosque.jpg', '', 9, 1, 1, 2, 220, 0, 40, '[{"value":3,"elementData":{"id":9,"label":"Flora","color":"48A819","icon":"/images/elements/nature.png"}}]', 16, 24, 3, NULL),
        (5, 5, 'Urgo el oso', '2025-09-21T11:16:19.154Z', NULL, 'urgo-el-oso', 'Vive en bosques frondosos. No es agresivo salvo que lo provoquen.', '/uploads/urgo-el-oso-1.jpg', '', 1, NULL, 4, 7, 250, 20, 0, '[{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 15, NULL, 10, NULL),
        (6, 6, 'Urgo el oso', '2025-09-21T11:17:58.200Z', NULL, 'urgo-el-oso', 'Es difícil verlo fuera de su hábitat. Si es visto, lo mejor es alejarse de el.', '/uploads/urgo-el-oso-2.jpg', '', 9, NULL, 4, 7, 300, 10, 0, NULL, 34, NULL, 10, NULL),
        (7, 7, 'Espada musgo', '2025-09-21T11:20:43.808Z', NULL, 'espada-musgo', 'Suele brotar en los claros de bosques donde viven <i>Hadas de los bosques</i>.', '/uploads/espada-musgo.jpg', '', 9, NULL, 5, 2, 120, 60, 10, '[{"value":2,"elementData":{"id":9,"label":"Flora","color":"48A819","icon":"/images/elements/nature.png"}}]', 24, NULL, 3, 6),
        (8, 8, 'El/la que brilla', '2025-09-21T11:26:21.154Z', NULL, 'ella-que-brilla', 'En ocasiones aparece algo parecido a un humanoide que irradia luz. Quien ha tenido la suerte de poder verlo disfruta de buena suerte.', '/uploads/el-que-brilla.jpg', '', 12, NULL, 1, 3, 90, 0, 0, '[{"value":3,"elementData":{"id":12,"label":"Luz","color":"E8E7D7","icon":"/images/elements/light.png"}}]', 25, NULL, 10, 1),
        (9, 9, 'Hombre lobo', '2025-09-21T11:33:16.578Z', NULL, 'hombre-lobo', 'Su fuerza depende de los ciclos lunares.', '/uploads/hombre-lobo.jpg', '', 1, NULL, 4, 7, 160, 20, 0, '[{"value":2,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 14, NULL, NULL, NULL),
        (10, 10, 'Moira', '2025-09-21T11:40:09.803Z', NULL, 'moira', 'Ser místico que es capaz de canalizar los elementos para aprovechar su poder.', '/uploads/moira-1.jpg', '', 13, 6, 3, 5, 240, 0, 20, '[{"value":2,"elementData":{"id":6,"label":"Hielo","color":"70D4DA","icon":"/images/elements/ice.png"}}]', 21, 40, 17, NULL),
        (11, 11, 'Moira', '2025-09-21T11:41:38.234Z', NULL, 'moira', 'Ser místico que es capaz de canalizar los elementos para aprovechar su poder.', '/uploads/moira-2.jpg', '', 13, 7, 3, 5, 190, 0, 0, '[{"value":2,"elementData":{"id":7,"label":"Rayo","color":"CBB734","icon":"/images/elements/thunder.png"}}]', 13, 40, 17, NULL),
        (12, 30, 'Espectro', '2025-09-21T11:45:00.000Z', NULL, 'espectro', 'Entidad espectral que acecha entre las sombras de los planos etéreos.', '/uploads/espectro.jpg', '', 1, NULL, 1, 7, 180, 0, 10, NULL, 16, NULL, NULL, NULL),
        (13, 12, 'Héroe', '2025-09-21T11:54:00.994Z', NULL, 'heroe', 'Héroe entre los mortales. Mucho que demostrar ante los inmortales.', '/uploads/guerrero-en-practicas.jpg', '', 1, NULL, 2, 4, 190, 10, 0, '[{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 15, 14, 11, 5),
        (14, 13, 'Heraldo del rayo', '2025-09-21T11:55:08.554Z', 13, 'heraldo-del-rayo', 'Cuando suena el trueno, el Heraldo del rayo está en camino.', '/uploads/heraldo-del-rayo.jpg', '', 7, NULL, 2, 2, 190, 20, 0, '[{"value":2,"elementData":{"id":7,"label":"Rayo","color":"CBB734","icon":"/images/elements/thunder.png"}}]', 13, 30, 10, NULL),
        (15, 14, 'Guerrero de la llama', '2025-09-21T11:58:03.036Z', 13, 'guerrero-de-la-llama', 'Cuando hizo su viaje al Hades no se esperaba resurgir con el poder de la llama.', '/uploads/guerrero_de_fuego.jpg', '', 5, NULL, 2, 2, 160, 20, 0, '[{"value":3,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}}]', 20, NULL, 12, NULL),
        (16, 15, 'Heraldo de Poseidón', '2025-09-21T12:00:28.368Z', 13, 'heraldo-de-poseidon', 'El dios Poseidón se percató del potencial de este guerrero otorgándole el poder de las mareas.', '/uploads/heraldo-del-poseidon.jpg', '', 3, NULL, 2, 2, 250, 0, 0, '[{"value":2,"elementData":{"id":3,"label":"Agua","color":"3E82B6","icon":"/images/elements/water.png"}}]', 19, NULL, NULL, NULL),
        (17, 16, 'Come metal', '2025-09-21T12:13:58.647Z', NULL, 'come-metal', 'Pequeño monstruo que busca constantemente objetos hechos de metal para alimentarse.', '/uploads/come-metal.jpg', '', 8, NULL, 4, 7, 180, 0, 0, NULL, 27, NULL, NULL, NULL),
        (18, 17, 'Devora metal', '2025-09-21T12:16:44.740Z', 17, 'devora-metal', 'Cuando <i>Come metal</i> crece, se ve en la necesidad de buscar estructuras de metal para alimentarse.', '/uploads/traga-metal.jpg', '', 8, NULL, 4, 2, 260, 0, 0, '[{"value":2,"elementData":{"id":8,"label":"Metal","color":"939393","icon":"/images/elements/metal.png"}}]', 27, 28, NULL, NULL),
        (19, 18, 'Dragón de la montaña', '2025-09-21T12:19:39.108Z', NULL, 'dragon-de-la-montana', 'Este dragón pacífico y de enorme tamaño se mimetiza con la montaña.', '/uploads/dragon-de-la-montaña.jpg', '', 2, NULL, 4, 3, 300, 30, 0, NULL, 31, NULL, 7, NULL),
        (20, 19, 'Jörmungandr', '2025-09-21T12:21:46.485Z', NULL, 'jormungandr', 'La serpiente del mundo. Leyenda de la mitología nórdica.', '/uploads/Jormungandr-1.jpg', '', 1, NULL, 4, 3, 320, 0, 0, NULL, 19, 32, 10, NULL),
        (21, 20, 'Jörmungandr', '2025-09-21T12:24:40.149Z', NULL, 'jormungandr', 'La serpiente del mundo. Leyenda de la mitología nórdica.', '/uploads/Jormungandr-3.jpg', '', 1, 3, 4, 3, 240, 20, 0, '[{"value":1,"elementData":{"id":1,"label":"Ether","color":"BCBCBC","icon":"/images/elements/ether.png"}}]', 19, 30, NULL, NULL),
        (22, 21, 'Cabeza de medusa', '2025-09-21T12:27:52.155Z', NULL, 'cabeza-de-medusa', 'Cabeza cercenada de una de las hermanas gorgonas.', '/uploads/cabeza-de-medusa.jpg', '', 13, NULL, 5, 3, 120, 0, 0, '[{"value":2,"elementData":{"id":13,"label":"Oscuridad","color":"2D2733","icon":"/images/elements/darkness.png"}}]', 40, NULL, 9, 7),
        (23, 22, 'Lumeiga', '2025-09-21T12:31:26.746Z', NULL, 'lumeiga', 'Cuando la tiraron a la hoguera descubrieron que hay brujas que no solo les afecta el fuego, si no que lo controlan.', '/uploads/lumeiga.jpg', '', 5, 13, 3, 2, 210, 0, 20, '[{"value":1,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}},{"value":1,"elementData":{"id":13,"label":"Oscuridad","color":"2D2733","icon":"/images/elements/darkness.png"}}]', 29, 41, 12, NULL),
        (24, 23, 'Extracto de ether', '2025-09-21T12:36:23.550Z', NULL, 'extracto-de-ether', 'Objeto que se usa en batalla para aumentar la salud.', '/uploads/extracto-de-ether.jpg', '', 1, NULL, 6, 7, 80, 0, 0, NULL, 16, NULL, 15, 10),
        (25, 24, 'Ego', '2025-09-21T14:44:05.603Z', NULL, 'ego', 'Sabio.', '/uploads/ego.jpg', '', 11, NULL, 3, 5, 90, 20, 40, '[{"value":2,"elementData":{"id":11,"label":"Mental","color":"D92FC5","icon":"/images/elements/mental.png"}}]', 26, 38, NULL, NULL),
        (26, 25, 'Nórdico', '2025-09-21T14:49:45.048Z', NULL, 'nordico', 'Monstruo de hielo del norte.', '/uploads/nordico.jpg', '', 6, NULL, 4, 7, 290, 0, 0, '[{"value":3,"elementData":{"id":6,"label":"Hielo","color":"70D4DA","icon":"/images/elements/ice.png"}}]', 35, NULL, 10, NULL),
        (27, 26, 'Paramo helado', '2025-09-21T14:52:37.853Z', NULL, 'paramo-helado', 'Cada vez hace más frio y hasta empieza a nevar.', '/uploads/paramo-helado.jpg', '', 6, NULL, 7, 2, 100, 0, 0, '[{"value":3,"elementData":{"id":6,"label":"Hielo","color":"70D4DA","icon":"/images/elements/ice.png"}}]', 35, NULL, 18, NULL),
        (28, 27, 'Volcán', '2025-09-21T14:57:17.279Z', NULL, 'volcan', 'Calor, humedad y olor a azufre.', '/uploads/volcan.jpg', '', 5, NULL, 7, 2, 1000, 0, 0, '[{"value":3,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}}]', 20, NULL, 19, NULL),
        (29, 28, 'Fénix', '2025-09-21T18:07:48.827Z', NULL, 'fenix', 'Renace de sus propias cenizas.', '/uploads/fenix.jpg', '', 5, NULL, 4, 3, 320, 0, 0, NULL, 20, NULL, 1, NULL),
        (30, 29, 'Herrero', '2025-09-21T18:14:48.743Z', NULL, 'herrero', 'Trabaja el metal y el fuego.', '/uploads/herrero.jpg', '', 8, 5, 5, 7, 80, 0, 0, '[{"value":1,"elementData":{"id":5,"label":"Fuego","color":"CB4634","icon":"/images/elements/fire.png"}},{"value":1,"elementData":{"id":8,"label":"Metal","color":"939393","icon":"/images/elements/metal.png"}}]', 28, NULL, 7, 9);
    """)

    # Update sequence for cards
    conn.exec_driver_sql("SELECT setval('cards_id_seq', (SELECT MAX(id) FROM cards));")


def downgrade() -> None:
    op.drop_table("cards")
    op.drop_table("attacks")
    op.drop_table("associations")
    op.drop_table("abilities")
    op.drop_table("characters")
    op.drop_table("types")
    op.drop_table("elements")
