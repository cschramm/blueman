# coding=utf-8

import dbus

from blueman.plugins.AppletPlugin import AppletPlugin
from operator import attrgetter


class MenuItem(object):
    def __init__(self, menu_plugin, owner, priority, text, markup, icon_name, tooltip, callback, submenu, visible):
        self._menu_plugin = menu_plugin
        self._owner = owner
        self._priority = priority
        self._text = text
        self._markup = markup
        self._icon_name = icon_name
        self._tooltip = tooltip
        self._callback = callback
        self._submenu = submenu
        self._visible = visible
        self._sensitive = True

        assert text and icon_name and (callback or submenu) or not any([text, icon_name, tooltip, callback, submenu])

    @property
    def owner(self):
        return self._owner

    @property
    def priority(self):
        return self._priority

    @property
    def callback(self):
        return self._callback

    @property
    def visible(self):
        return self._visible

    def __iter__(self):
        # TODO: submenu
        for key in ['text', 'markup', 'icon_name', 'tooltip', 'sensitive']:
            value = getattr(self, '_' + key)
            if value is not None:
                yield key, value

    def set_text(self, text, markup=False):
        self._text = text
        self._markup = markup
        self._menu_plugin.on_menu_changed()

    def set_icon_name(self, icon_name):
        self._icon_name = icon_name
        self._menu_plugin.on_menu_changed()

    def set_tooltip(self, tooltip):
        self._tooltip = tooltip
        self._menu_plugin.on_menu_changed()

    def set_visible(self, visible):
        self._visible = visible
        self._menu_plugin.on_menu_changed()

    def set_sensitive(self, sensitive):
        self._sensitive = sensitive
        self._menu_plugin.on_menu_changed()


class Menu(AppletPlugin):
    __description__ = _("Provides a menu for the applet and an API for other plugins to manipulate it")
    __icon__ = "menu-editor"
    __author__ = "Walmis"
    __unloadable__ = False

    def on_load(self, applet):
        self.Applet = applet

        self.__plugins_loaded = False

        self.__menuitems = []

    def __sort(self):
        self.__menuitems.sort(key=attrgetter('priority'))

    def add(self, owner, priority, text=None, markup=False, icon_name=None, tooltip=None, callback=None, submenu=None,
            visible=True):
        item = MenuItem(self, owner, priority, text, markup, icon_name, tooltip, callback, submenu, visible)
        self.__menuitems.append(item)
        if self.__plugins_loaded:
            self.__sort()
        self.on_menu_changed()
        return item

    def unregister(self, owner):
        for item in reversed(self.__menuitems):
            if item.owner == owner:
                self.__menuitems.remove(item)
        self.on_menu_changed()

    def on_plugins_loaded(self):
        self.__plugins_loaded = True
        self.__sort()

    def on_menu_changed(self):
        self.MenuChanged(self.GetMenu())

    @dbus.service.signal('org.blueman.Applet', signature='aa{sv}')
    def MenuChanged(self, menu):
        pass

    @dbus.service.method('org.blueman.Applet', in_signature='', out_signature='aa{sv}')
    def GetMenu(self):
        return [dict(item) for item in self.__menuitems if item.visible]

    @dbus.service.method('org.blueman.Applet', in_signature='i', out_signature='')
    def ActivateMenuItem(self, index):
        [item for item in self.__menuitems if item.visible][index].callback()
