from models import Player, Alliance, UsedName, Identity, IdentityLinkage, db


@db.atomic()
def update_name(player, name):
    if player.current_name != name:
        player.current_name = name
        player.save()
        UsedName.create(player=player, name=name)
        return True


@db.atomic()
def create_new_player(gov_id, name):
    player = Player.create(gov_id=gov_id, current_name=name)
    UsedName.create(player=player, name=name)
    return player


@db.atomic()
def update_player(gov_id, name, alliance=None, discord_id=None):
    # create player
    player = Player.get_or_none(gov_id=gov_id)
    if not player:
        player = create_new_player(gov_id, name)
        print('created', gov_id)

    # update alliance
    if isinstance(alliance, str):
        alliance = Alliance.get(name=alliance.strip())
    if isinstance(alliance, Alliance):
        player.alliance = alliance
        player.save()

    # update name
    if update_name(player, name):
        print(f'renamed {player.current_name}  => {name}')

    if discord_id:
        identity, _ = Identity.get_or_create(external_id=discord_id)
        linkage = IdentityLinkage.filter(player=player).order_by(IdentityLinkage.id.desc()).first()
        if not linkage:
            IdentityLinkage.create(player=player, identity=identity)
        elif linkage.identity != identity:
            raise ValueError(f'{gov_id=} already linked to {linkage.identity.external_id=} ')

    return player
