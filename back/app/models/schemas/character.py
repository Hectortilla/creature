from app.models.base.character import CharacterBase


class CharacterCreate(CharacterBase):
    pass


class CharacterRead(CharacterBase):
    id: int
