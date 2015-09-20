# -*- coding: utf-8 -*-
#
# Copyright 2008-2010 Brett Adams
# Copyright 2015 Mario Frasca <mario@anche.no>.
#
# This file is part of bauble.classic.
#
# bauble.classic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bauble.classic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bauble.classic. If not, see <http://www.gnu.org/licenses/>.

import bauble.pluginmgr as pluginmgr


class PrefsCommandHandler(pluginmgr.CommandHandler):

    command = ('prefs', 'config')
    view = None

    def __call__(self, cmd, arg):
        pass

    def get_view(self):
        if self.view is None:
            self.view = LogView()
        return self.view


pluginmgr.register_command(PrefsCommandHandler)

prefs = _prefs()
