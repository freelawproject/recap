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
// JSON serialization.

using System;
using System.Web.Script.Serialization;

namespace RECAP {
    public static class JSON {

        private static JavaScriptSerializer serializer = new JavaScriptSerializer();

        public static string Stringify(object o) {
            return serializer.Serialize(o);
        }

        public static object Parse(string s) {
            return serializer.DeserializeObject(s);
        }

        public static object Parse(string s, Type t) {
            return serializer.Deserialize(s, t);
        }

    }
}
