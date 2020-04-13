from dbus_media_player import DbusMediaPlayer


class DbusMediaPlayerMonitor:
    MEDIA_PLAYER_PREFIX = 'org.mpris.MediaPlayer2.'

    _active_player_changed_callback = None

    def __init__(self, session_bus) -> None:
        self._bus = session_bus
        self._active_player = None
        self._player_list = {}

        for name in session_bus.list_names():
            if name.startswith(self.MEDIA_PLAYER_PREFIX):
                owner = self._bus.get_name_owner(name)
                self._add_player(name, owner)

        self._bus.add_signal_receiver(self._name_owner_changed, 'NameOwnerChanged')

    def get_active(self) -> DbusMediaPlayer:
        if self._active_player:
            return self._player_list[self._active_player]
        return None

    def _name_owner_changed(self, name, old_owner, new_owner):
        if name.startswith(self.MEDIA_PLAYER_PREFIX):
            if new_owner and not old_owner:
                self._add_player(name, new_owner)
            elif old_owner and not new_owner:
                self._remove_player(name, old_owner)
            else:
                self._change_player_owner(name, old_owner, new_owner)

    def _add_player(self, name, owner):
        self._player_list[owner] = DbusMediaPlayer(self._bus, name, owner)
        if self._active_player is None:
            self._active_player = owner
            if self._active_player_changed_callback:
                self._active_player_changed_callback(self._player_list[owner])

    def _remove_player(self, name, owner):
        if self._player_list[owner] and self._player_list[owner].bus_name == name:
            del self._player_list[owner]

        if self._active_player == owner:
            self._active_player = None
            for key in self._player_list.keys():
                self._active_player = key
            if self._active_player:
                self._active_player_changed_callback(self._player_list[self._active_player])
            else:
                self._active_player_changed_callback(None)

    def _change_player_owner(self, name, old_owner, new_owner):
        if self._player_list[old_owner] and self._player_list[old_owner].bus_name == name:
            self._player_list[new_owner] = self._player_list[old_owner]
            self._player_list[new_owner].owner = new_owner
            del self._player_list[old_owner]
            if self._active_player == old_owner:
                self._active_player = new_owner

    def set_active_player_changed_callback(self, callback):
        self._active_player_changed_callback = callback

    def select_previous_player(self):
        keys = list(self._player_list.keys())
        index = keys.index(self._active_player)
        if index == 0:
            index = len(keys)
        self._active_player = keys[(index - 1) % len(keys)]
        self._active_player_changed_callback(self._player_list[self._active_player])

    def select_next_player(self):
        keys = list(self._player_list.keys())
        self._active_player = keys[(keys.index(self._active_player) + 1) % len(keys)]
        self._active_player_changed_callback(self._player_list[self._active_player])
