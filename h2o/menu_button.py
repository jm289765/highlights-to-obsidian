from functools import partial
from calibre.gui2.actions import InterfaceAction
from calibre_plugins.highlights_to_obsidian.main import MainDialog
import calibre_plugins.highlights_to_obsidian.button_actions as b_acts


class MenuButton(InterfaceAction):
    name = 'Send Highlights to Obsidian'
    action_add_menu = True

    #: Of the form: (text, icon_path, tooltip, keyboard shortcut).
    # If you pass an empty tuple, then the shortcut is registered with no default key binding.
    # to add more actions, call self.create_action() with one a tuple of this format as input
    action_spec = ('H2O', None,
                   'Highlights to Obsidian Menu', None)

    def __init__(self, parent, site_customization):
        super().__init__(parent, site_customization)
        self.new_highlights_action = None
        self.all_highlights_action = None
        self.resend_highlights_action = None
        self.user_config_action = None
        self.open_help_action = None

    def genesis(self):
        # This method is called once per plugin, do initial setup here

        # Set the icon for this interface action
        # The get_icons function is a builtin function defined for all your
        # plugin code. It loads icons from the plugin zip file. It returns
        # QIcon objects, if you want the actual data, use the analogous
        # get_resources builtin function.
        #
        # Note that if you are loading more than one icon, for performance, you
        # should pass a list of names to get_icons. In this case, get_icons
        # will return a dictionary mapping names to QIcons. Names that
        # are not found in the zip file will result in null QIcons.

        # highlights_to_obsidian doesn't currently have an icon
        # todo: make menu icon for this plugin
        # icon = get_icons('images/icon.png', 'Interface Demo Plugin')

        # The qaction is automatically created from the action_spec defined
        # above
        # self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_dialog)

        # action specs are of the form: (text, icon_path, tooltip, keyboard shortcut).
        ma = partial(self.create_menu_action, self.qaction.menu())
        un = "Highlights to Obsidian: Menu Button: "
        # create_menu_action(self, menu, unique_name, text, icon=None, shortcut=None,
        #             description=None, triggered=None, shortcut_name=None, persist_shortcut=False):
        nh = "Send New Highlights to Obsidian"
        nhd = "Send new highlights to Obsidian"
        self.new_highlights_action = ma(un + nh, nh, description=nhd, shortcut=None, triggered=self.send_new)
        ah = "Send All Highlights to Obsidian"
        ahd = "Send all highlights to Obsidian"
        self.all_highlights_action = ma(un + ah, ah, description=ahd, shortcut=None, triggered=self.send_all)
        rh = "Resend Highlights to Obsidian"
        rhd = "Resend last highlights sent to Obsidian"
        self.resend_highlights_action = ma(un + rh, rh, description=rhd, shortcut=None, triggered=self.resend)
        ocd = "Open config settings for Highlights to Obsidian"
        self.user_config_action = ma(un + "Config", "Config", description=ocd, shortcut=False, triggered=self.open_config)
        hd = "Open help menu for Highlights to Obsidian"
        self.open_help_action = ma(un + "Help", "Help", description=hd, shortcut=False, triggered=self.open_help)

    def show_dialog(self):
        # The base plugin object defined in __init__.py
        base_plugin_object = self.interface_action_base_plugin
        do_user_config = base_plugin_object.do_user_config

        d = MainDialog(self.gui, self.qaction.icon(), do_user_config)
        d.show()

    def send_new(self):
        b_acts.send_new_highlights(self.gui, self.gui.current_db.new_api)

    def send_all(self):
        b_acts.send_all_highlights(self.gui, self.gui.current_db.new_api)

    def resend(self):
        b_acts.resend_highlights(self.gui, self.gui.current_db.new_api)

    def open_config(self):
        do_user_config = self.interface_action_base_plugin.do_user_config
        do_user_config(parent=self.gui)

    def open_help(self):
        b_acts.help_menu(self.gui)

    def apply_settings(self):
        from calibre_plugins.highlights_to_obsidian.config import prefs
        # apply relevant config settings
        pass