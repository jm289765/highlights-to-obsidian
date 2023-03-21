# this plugin's code is based on Kovid Goyal's example plugin at
# https://manual.calibre-ebook.com/creating_plugins.html

from calibre.customize import InterfaceActionBase

_version = (1, 3, 3)
version = ".".join([str(x) for x in _version])


class HighlightsToObsidianPlugin(InterfaceActionBase):
    name                = 'Highlights to Obsidian'
    description         = 'Automatically send highlights from calibre to obsidian.md'
    supported_platforms = ['windows', 'osx', 'linux']  # only tested on windows
    author              = 'jm289765'
    version             = _version
    actual_plugin       = 'calibre_plugins.highlights_to_obsidian.menu_button:MenuButton'
    minimum_calibre_version = (6, 10, 0)  # this plugin probably works on earlier versions, i haven't tested

    def is_customizable(self):
        return True

    def config_widget(self):
        # don't move this import statement
        from calibre_plugins.highlights_to_obsidian.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()

        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()
