// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// ------------------
// An abstract interface that *must* be implemented for BHOs.

using System;
using System.Runtime.InteropServices;

namespace RECAP {
    [
        ComVisible(true),
        InterfaceType(ComInterfaceType.InterfaceIsIUnknown),
        Guid("FC4801A3-2BA9-11CF-A229-00AA003D7352")
    ]
    public interface IObjectWithSite {

        [PreserveSig]
        int SetSite([MarshalAs(UnmanagedType.IUnknown)] object site);

        [PreserveSig]
        int GetSite(ref Guid guid, out IntPtr ppvSite);

    }
}