﻿using System.IO;
using System.Collections.Generic;

namespace RECAP {
    public class FormData {
        
        private const string boundary = "ce15f4e5-9e5c-43f3-b44f-a5913573838d";

        private List<Part> parts;

        public FormData() {
            this.parts = new List<Part>();
        }

        public void Append(string key, string value) {
            this.parts.Add(new Part(key, value, null, null));
        }

        public void Append(string key, object value, string filename, string mimetype) {
            this.parts.Add(new Part(key, value, filename, mimetype));
        }

        public void Write(Stream stream) {
            foreach (Part part in this.parts) {
                if (part.filename == null || part.mimetype == null)
                    this.WriteString(stream, part);
                else
                    this.WriteFile(stream, part);
            }
            this.WriteBoundary(stream, true);
        }

        private void WriteString(Stream stream, Part part) {
            this.WriteBoundary(stream);
            this.WriteDisposition(stream, part.key);
            this.WriteLine(stream);
            this.WriteLine(stream, (string) part.value);
        }

        private void WriteFile(Stream stream, Part part) {
            this.WriteBoundary(stream);
            this.WriteDisposition(stream, part.key, part.filename);
            this.WriteType(stream, part.mimetype);
            this.WriteLine(stream);
            this.WriteLine(stream, part.value.ToString());
        }

        private void WriteBoundary(Stream stream) {
            this.WriteBoundary(stream, false);
        }

        private void WriteBoundary(Stream stream, bool end) {
            string line = "--" + boundary;
            if (end) line += "--";
            (new StreamWriter(stream)).WriteLine(line);
        }

        private void WriteDisposition(Stream stream, string name) {
            (new StreamWriter(stream)).WriteLine("Content-Dispostion: form-data; name=\"" + name + "\"");
        }

        private void WriteDisposition(Stream stream, string name, string filename) {
            (new StreamWriter(stream)).WriteLine("Content-Dispostion: form-data; name=\"" + name + "\"; filename=\"" + filename + "\"");
        }

        private void WriteType(Stream stream, string mimetype) {
            (new StreamWriter(stream)).WriteLine("Content-Type: " + mimetype);
        }

        private void WriteLine(Stream stream) {
            (new StreamWriter(stream)).WriteLine();
        }

        private void WriteLine(Stream stream, string text) {
            (new StreamWriter(stream)).WriteLine(text);
        }

        private class Part {

            public string key;
            public object value;
            public string filename;
            public string mimetype;

            public Part(string key, object value, string filename, string mimetype) {
                this.key = key;
                this.value = value;
                this.filename = filename;
                this.mimetype = mimetype;
            }

        }

    }
}