// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// The RECAP IE Extension is free software: you can redistribute it 
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation, either version 3 of the 
// License, or (at your option) any later version.
//
// The RECAP IE Extension is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with the RECAP IE Extension.  If not, see: 
// http://www.gnu.org/licenses/
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