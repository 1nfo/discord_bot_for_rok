from fuzzywuzzy import process

from models import Player, Alliance, UsedName, Identity, IdentityLinkage, db


def get_player_by_id(gov_id):
    return Player.get_or_none(gov_id=gov_id)


def get_identity_by_gov_id(gov_id):
    linkage = IdentityLinkage.select().join(Player).where(
        Player.gov_id == gov_id
    ).order_by(IdentityLinkage.datetime_created.desc()).first()
    return linkage.identity if linkage else None


def get_player_by_discord_id(discord_id):
    linkage = IdentityLinkage.select().join(Identity).where(
        (Identity.external_id == discord_id) & (Identity.type == Identity.Type.Discord)
    ).order_by(IdentityLinkage.type.asc()).first()
    return linkage.player if linkage else None


def get_players_by_discord_id(discord_id):
    return list(IdentityLinkage.select().join(Identity).where(
        (Identity.external_id == discord_id) & (Identity.type == Identity.Type.Discord)
    ).order_by(IdentityLinkage.type.asc()))


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

    player = get_player_by_id(gov_id)
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
def upsert_player(gov_id, name, alliance=None, discord_id=None):
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
        linkages = IdentityLinkage.filter(identity=identity)
        # first linkage, assume it is main
        if not linkages.exists():
            linkage_type = IdentityLinkage.Type.Main
        # make sure it is not linked already
        elif not linkages.filter(player=player).exists():
            linkage_type = IdentityLinkage.Type.Sub
        else:
            return player
        # remove linkage player to others to guarantee only it links to one identity
        IdentityLinkage.create(player=player, identity=identity, type=linkage_type)
        add_player_note(gov_id, 'INFO', f'linked to discord {identity.external_id}')

    return player


def _fuzzy_match(name, chooses):
    result = process.extractOne(name, chooses, score_cutoff=60)
    return result and result[0]
