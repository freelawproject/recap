// This file is part of RECAP for IE.
// Copyright (C) 2013 Ying Lei <ying.lei@live.com>
//
// ------------------
// JSON serializer using data contracts.
//
// Usage (DataContract definition):
//
//     using System.Runtime.Serialization;
//
//     [DataContract]
//     public class CaseQueryRequest {
//
//         [DataMember]
//         public string court;
//         [DataMember]
//         public string casenum;
//
//         public CaseQueryRequest(string court, string casenum) {
//             this.court = court;
//             this.casenum = casenum;
//         }
//
//     }
//
// Usage (serialization):
//
//     string json = JSON.Stringify(new CaseQueryRequest("example-court", "example-case-number"));
//
// Usage (deserialization):
//
//     CaseQueryRequest request = (CaseQueryRequest) JSON.Parse(json, typeof(CaseQueryRequest));

using System;
using System.IO;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;

namespace RECAP {
    public static class JSON {

        public static object Parse(string s, Type t) {
            MemoryStream stream = new MemoryStream();
            DataContractJsonSerializer serializer = new DataContractJsonSerializer(t);
            (new StreamWriter(stream)).Write(s);
            return serializer.ReadObject(stream);
        }

        public static string Stringify(object o, Type t) {
            MemoryStream stream = new MemoryStream();
            DataContractJsonSerializer serializer = new DataContractJsonSerializer(t);
            serializer.WriteObject(stream, o);
            return (new StreamReader(stream)).ReadToEnd();
        }

        public static string Stringify(object o) {
            return Stringify(o, o.GetType());
        }

    }
}