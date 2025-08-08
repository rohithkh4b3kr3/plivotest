import React, { useState } from "react";

export default function Summarizer() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUrl("");
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
    setFile(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    const fd = new FormData();
    if (file) fd.append("file", file);
    else if (url.trim()) fd.append("url", url);
    else {
      alert("Please select a file or enter a URL");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("http://localhost:5000/summarize", {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      if (data.summary) setSummary(data.summary);
      else alert(data.error || "Failed to summarize");
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif" }}>
      <h1>Document / URL Summarizer</h1>

      <div>
        <input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
      </div>
      <div style={{ margin: "10px 0" }}>
        <input
          type="text"
          placeholder="Or paste a URL here"
          value={url}
          onChange={handleUrlChange}
          style={{ width: "300px", padding: "5px" }}
        />
      </div>
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Summarizing..." : "Get Summary"}
      </button>

      {summary && (
        <div style={{ marginTop: 20 }}>
          <h3>Summary</h3>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
}
