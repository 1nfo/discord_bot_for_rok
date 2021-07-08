class GuildSettings:
    _instances = []

    @classmethod
    def get(cls, **kwargs):
        if kwargs:
            for i in cls._instances:
                for k, v in kwargs.items():
                    if v != getattr(i, k, None):
                        break
                else:
                    return i

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self._instances.append(self)

    def get_channel(self, target):
        return self.channels[target]


GuildSettings(
    id=809851791265103913,
    name='kingdom',
    officer_role_id=809851791294201878,
    approver_role_id=809851791294201878,
    request_role_id=809851791294201876,
    channels={
        'linkme': 862607708179267594,
        'mykill': 862609422752677938,
        'myhonor': 862609554671009842,
        'myscore': 862609478263767051,
    },
)

GuildSettings(
    id=796434423263395850,
    name='leo',
    officer_role_id=796906896316432385,
    approver_role_id=796906896316432385,
    request_role_id=796905931794284564,
    kill_channel_id=827548764050161684,
    honor_channel_id=832151996030124053,
    prekvk_channel_ids=[827226738634391642, 827548553568059454, 827548617937780766],
    channels={
        'kill': 827548764050161684,
        'honor': 832151996030124053,
        'prekvk1': 827226738634391642,
        'prekvk2': 827548553568059454,
        'prekvk3': 827548617937780766,
    },
)

GuildSettings(
    id=825806916507926569,
    name='test',
    officer_role_id=858884620456165378,
    approver_role_id=858884620456165378,
    request_role_id=858884620456165378,
    kill_channel_id=825807687517601842,
    honor_channel_id=825807687517601842,
    prekvk_channel_ids=[825807687517601842, 825807687517601842, 825807687517601842],
    channels={
        'linkme': 825807687517601842,
        'mykill': 825807687517601842,
        'myhonor': 825807687517601842,
        'myscore': 825807687517601842,
    },
)
