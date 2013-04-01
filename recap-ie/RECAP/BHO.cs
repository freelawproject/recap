// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// ------------------
// The Browser Helper Object (BHO) -- i.e., "extension" in IE-speak.
//
// The IObjectWithSite interface implemented below loads RECAP if the URL
// indicates a PACER-related webpage.

using System;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using SHDocVw;
using MSHTML;

namespace RECAP {
    [
        ComVisible(true),
        Guid("ce15f4e5-9e5c-43f3-b44f-a5913573838d"),  // Generated with System.Guid.NewGuid()
        ClassInterface(ClassInterfaceType.None)
    ]
    public class BHO : IObjectWithSite {

        private WebBrowser browser;
        private RECAP recap;

        // IObjectSite interface
            
        public int SetSite(object site) {
            if (site != null) {
                this.browser = (WebBrowser) site;
                this.browser.DocumentComplete += new DWebBrowserEvents2_DocumentCompleteEventHandler(this.OnDocumentComplete);
                this.recap = new RECAP(this.browser);
            } else {
                this.browser.DocumentComplete -= new DWebBrowserEvents2_DocumentCompleteEventHandler(this.OnDocumentComplete);
                this.browser = null;
                this.recap = null;
            }
            return 0;
        }

        public int GetSite(ref Guid guid, out IntPtr ppvSite) {
            IntPtr p = Marshal.GetIUnknownForObject(browser);
            int hr = Marshal.QueryInterface(p, ref guid, out ppvSite);
            Marshal.Release(p);
            return hr;
        }


        // DocumentComplete handler

        void OnDocumentComplete(object pDisp, ref object URL) {
            this.recap.ProcessDocument();
        }


        // Registry install / uninstall

        public const string BHO_REGISTRY_KEY_NAME = "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Browser Helper Objects";

        // Install command: `C://Windows/[.NET]/regasm.exe recap.dll`
        [ComRegisterFunction]
        public static void RegisterBHO(Type type) {

            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(BHO_REGISTRY_KEY_NAME, true);
            if (registryKey == null) {
                registryKey = Registry.LocalMachine.CreateSubKey(BHO_REGISTRY_KEY_NAME);
            }

            string guid = type.GUID.ToString("B");
            RegistryKey ourKey = registryKey.OpenSubKey(guid);
            if (ourKey == null) {
                ourKey = registryKey.CreateSubKey(guid);
            }

            ourKey.SetValue("NoExplorer", 1, RegistryValueKind.DWord);

            registryKey.Close();
            ourKey.Close();

        }

        // Uninstall command: `C://Windows/[.NET]/regasm.exe /u recap.dll`
        [ComUnregisterFunction]
        public static void UnregisterBHO(Type type) {
            RegistryKey registryKey = Registry.LocalMachine.OpenSubKey(BHO_REGISTRY_KEY_NAME, true);
            string guid = type.GUID.ToString("B");
            if (registryKey != null) {
                registryKey.DeleteSubKeyTree(guid);
                registryKey.Close();
            }
        }

    }
}