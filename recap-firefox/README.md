Overview
========
The RECAP Firefox Extension.
Website: https://www.recapthelaw.org
Contact: info@recapthelaw.org


For Developers
===============
Building your own version
-------------
To build a modified and signed version of this extension, simply run build.sh.


Setting up your Environment
-------
You'll probably want a Firefox dev environment set up. This gets complicated,
but there are some great resources out there. As more details are collected,
please update this section.

To set up a Firefox dev environment:

1. Once you've got RECAP installed, go to [about:config][about] and search for 
   the option extensions.recap.developer_mode and toggle it to true. This 
   changes the extension so that your uploads and experiments do not hit the 
   live API and instead are sent to our development machine. This was [fixed in
   issue #24][24].

1. Follow [the instructions on Mozilla's website][mdn] for setting up a development
   profile. You can mostly ignore the extensions that it wants you to install.

1. To make it so you don't have to build and reinstall RECAP all the time, you
   should create an ["Extension Proxy File"][proxy]. Once that's done, all you
   have to do is restart Firefox to get updated code. That, in turn, can be
   simplified with the [Restartless Restart Add-On][ramo].

Tips
-----
1. Once you've got the settings above in place, you can debug the browser XUL
and JavaScript by going to Tools > Web Developer > Browser Toolbox.

1. While it's true that every court has their own customized version of PACER,
   there is [a PACER training site that does not charge fees][trainwreck]. You
   can use this if you wish to work on the system without accruing charges.


Copyright & License
===================
Copyright 2009-2010 Harlan Yu, Timothy B. Lee, Stephen Schultze, Dhruv Kapadia.

License:
    The RECAP Firefox Extension is free software: you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    The RECAP Firefox Extension is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with the RECAP Firefox Extension.  If not, see:
    http://www.gnu.org/licenses/


[mdn]: https://developer.mozilla.org/en-US/Add-ons/Setting_up_extension_development_environment
[trainwreck]: https://dcecf.psc.uscourts.gov/cgi-bin/login.pl
[proxy]: http://stackoverflow.com/questions/1077719/fastest-way-to-debug-firefox-addons-during-development
[ramo]: https://addons.mozilla.org/en-us/firefox/addon/restartless-restart/
[about]: http://about:config
[24]: https://github.com/freelawproject/recap-firefox/issues/24
