// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
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
