RECAP for IE
============

*A RECAP extension for Internet Explorer*



Resources
---------

* [RECAP Home Page][1]
* [RECAP Developer Slides][2]

[1]: https://www.recapthelaw.org/
[2]: https://docs.google.com/presentation/d/1khhCaQIC2bBSgZPmdskA5ONisDjiHU6a_50t7oYAKJU/



Status
------

WARNING: This extension has yet to be completed.

In particular, the following remains to be done:

* Making methods that make HTTP requests in `class RECAP()` asynchronous.
* Debugging interactions with PACER websites.
* Creating an installation package using NSIS.



Installation
------------

Currently, the extension must be installed manually:

1. Open Command Prompt using admnistrator privileges.
2. Find `RegAsm.exe` in a .NET v4.0 directory.
3. Navigate to the directory containing the compiled `RECAP.dll`.
4. Run `RegAsm.exe /codebase RECAP.dll`.

Once installed, "RECAP.BHO" should appear in IE as an add-on.


To uninstall manually:

1. Open Command Prompt using admnistrator privileges.
2. Find `RegAsm.exe` in a .NET v4.0 directory.
3. Navigate to the directory containing the compiled `RECAP.dll`.
4. Run `RegAsm.exe /unregister RECAP.dll`.


`RegAsm.exe` is usually found in directories like these:

    C:\Windows\Microsoft.NET\Framework\v4.0.xxxxx\RegAsm.exe
    C:\Windows\Microsoft.NET\Framework64\v4.0.xxxxx\RegAsm.exe

(For 32-bit IE and 64-bit IE, respectively.)


The compiled `RECAP.dll` can be found under the `bin` directory:

    .\RECAP\bin\Release\RECAP.dll



License
-------

The RECAP IE Extension is free software: you can redistribute it 
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

The RECAP IE Extension is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with the RECAP IE Extension.  If not, see: 
http://www.gnu.org/licenses/
