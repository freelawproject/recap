RECAP for IE
============

*A RECAP extension for Internet Explorer*



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
