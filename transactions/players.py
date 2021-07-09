from fuzzywuzzy import process

from models import Player, Alliance, UsedName, Identity, IdentityLinkage, db


def get_player(gov_id):
    return Player.get(gov_id=gov_id)


def search_player(name):
    if name.isdigit():
        q = Player.filter(gov_id=name)
    else:
        q = Player.filter(current_name=name)

    if q.count() == 1:
        return q.get(), []

    matched = list(filter(lambda x: name.lower() in x.name.lower(), UsedName.select()))
    if len(matched) == 1:
        return matched[0].player, []

    if 1 < len(matched) <= 5:
        return None, [x.name for x in matched]

    closest_name = _fuzzy_match(name, [x.name for x in UsedName.select()])
    return None, [closest_name] if closest_name else []


@db.atomic()
def update_name(gov_id, name):
    from transactions.notes import add_player_note

    player = get_player(gov_id)
    if player.current_name != name:
        old_name = player.current_name
        player.current_name = name
        player.save()
        UsedName.create(name=name, player=player)
        add_player_note(gov_id, 'INFO', f'renamed {old_name}  => {name}')
        return True


@db.atomic()
def create_new_player(gov_id, name):
    player = Player.create(gov_id=gov_id, current_name=name)
    UsedName.create(player=player, name=name)
    return player


@db.atomic()
def update_player(gov_id, name, alliance=None, discord_id=None):
    from transactions.notes import add_player_note

    # create player
    player = Player.get_or_none(gov_id=gov_id)
    if not player:
        player = create_new_player(gov_id, name)

    # update alliance
    if isinstance(alliance, str):
        alliance = Alliance.get(name=alliance.strip())
    if isinstance(alliance, Alliance):
        old_alliance = player.alliance
        player.alliance = alliance
        player.save()
        if old_alliance:
            add_player_note(gov_id, 'INFO', f'changed alliance {old_alliance.name}  => {alliance.name}')

    if discord_id:
        identity, _ = Identity.get_or_create(external_id=discord_id)
        linkage = IdentityLinkage.filter(player=player).order_by(IdentityLinkage.datetime_created.desc()).first()
        if not linkage:
            _, created = IdentityLinkage.get_or_create(player=player, identity=identity)
            if created:
                add_player_note(gov_id, 'INFO', 'linked to discord')
        elif linkage.identity != identity:
            raise ValueError(f'{gov_id=} already linked to {linkage.identity.external_id=} ')

    return player


def _fuzzy_match(name, chooses):
    result = process.extractOne(name, chooses, score_cutoff=60)
    return result and result[0]
