from models import db, Alliance


@db.atomic()
def create_new_alliance(name):
    return Alliance.create(name)


@db.atomic()
def list_all_alliance_names():
    return [a.name for a in Alliance.select()]


def get_alliance(name):
    return Alliance.get_or_none(name=name)


@db.atomic()
def update_alliance(player, alliance):
    from transactions.notes import add_player_note

    if isinstance(alliance, str):
        alliance = get_alliance(name=alliance.strip())
        if alliance is None:
            return False

    if player.alliance != alliance:
        old_alliance = player.alliance
        player.alliance = alliance
        player.save()
        add_player_note(player.gov_id, 'INFO', f'changed alliance {old_alliance}  => {alliance.name}')
        return True
