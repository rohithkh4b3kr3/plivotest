import React, { useState } from "react";

export default function App() {
  const [activeTab, setActiveTab] = useState("yolo");

  // YOLO States
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Summarizer States
  const [sumFile, setSumFile] = useState(null);
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [sumLoading, setSumLoading] = useState(false);

  // YOLO Functions
  function onFileChange(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
  }

  async function upload() {
    if (!file) return alert("Choose an image first");
    setLoading(true);
    const fd = new FormData();
    fd.append("image", file);
    try {
      const res = await fetch("http://localhost:5000/analyze", {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  // Summarizer Functions
  const handleSumFileChange = (e) => {
    setSumFile(e.target.files[0]);
    setUrl("");
  };

  const handleUrlChange = (e) => {
    setUrl(e.target.value);
    setSumFile(null);
  };

  const handleSummarize = async () => {
    setSumLoading(true);
    const fd = new FormData();
    if (sumFile) fd.append("file", sumFile);
    else if (url.trim()) fd.append("url", url);
    else {
      alert("Please select a file or enter a URL");
      setSumLoading(false);
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
      setSumLoading(false);
    }
  };

  return (
    // Container with animated background in dark gray and green theme
    <div className="min-h-screen bg-gradient-to-r from-gray-900 via-green-900 to-gray-800 overflow-hidden relative text-gray-300 font-sans flex flex-col items-center p-6">
      {/* Animated subtle background */}
      <div className="absolute inset-0 -z-10">
        <svg
          className="w-full h-full animate-spin-slow"
          viewBox="0 0 400 400"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="200" cy="200" r="180" stroke="#047857" strokeWidth="2" opacity="0.2" />
          <circle cx="200" cy="200" r="150" stroke="#10B981" strokeWidth="1" opacity="0.3" />
          <circle cx="200" cy="200" r="120" stroke="#059669" strokeWidth="0.5" opacity="0.4" />
        </svg>
      </div>

      {/* Header */}
      <h1 className="text-4xl font-bold mb-6 select-none text-green-400 drop-shadow-lg">
        AI Playground
      </h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-8">
        <button
          onClick={() => setActiveTab("yolo")}
          className={`px-6 py-2 rounded-md font-semibold transition-colors duration-300 focus:outline-none ${
            activeTab === "yolo"
              ? "bg-green-600 text-gray-100 shadow-md shadow-green-700"
              : "bg-gray-700 text-gray-400 hover:bg-green-700 hover:text-white"
          }`}
          aria-label="Switch to YOLO Analyzer tab"
        >
          YOLO Analyzer
        </button>
        <button
          onClick={() => setActiveTab("summarizer")}
          className={`px-6 py-2 rounded-md font-semibold transition-colors duration-300 focus:outline-none ${
            activeTab === "summarizer"
              ? "bg-green-600 text-gray-100 shadow-md shadow-green-700"
              : "bg-gray-700 text-gray-400 hover:bg-green-700 hover:text-white"
          }`}
          aria-label="Switch to Document Summarizer tab"
        >
          Summarizer
        </button>
      </div>

      {/* YOLO Tab */}
      {activeTab === "yolo" && (
        <div className="w-full max-w-3xl bg-gray-900 bg-opacity-60 rounded-lg p-6 shadow-lg">
          <h2 className="text-2xl font-semibold mb-4 text-green-300">YOLO Image Analyzer</h2>
          <input
            type="file"
            accept="image/*"
            onChange={onFileChange}
            className="block mb-4 text-gray-300 file:bg-green-700 file:text-white file:px-4 file:py-2 file:rounded cursor-pointer focus:ring-2 focus:ring-green-500"
          />
          {preview && (
            <div className="mb-4">
              <img
                src={preview}
                alt="preview"
                className="max-w-full max-h-96 rounded-lg border border-green-600 shadow-md"
              />
            </div>
          )}
          <button
            onClick={upload}
            disabled={loading || !file}
            className="px-5 py-2 bg-green-600 rounded-md text-gray-100 font-semibold hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed transition-all shadow-md focus:ring-2 focus:ring-green-400"
          >
            {loading ? "Analyzing..." : "Analyze Image"}
          </button>

          {result && (
            <div className="mt-8 text-gray-300">
              {result.error ? (
                <div className="bg-red-800 p-4 rounded-md text-red-300 font-mono whitespace-pre-wrap">
                  <h3 className="text-xl font-bold mb-2">Error</h3>
                  <pre>{result.error}</pre>
                </div>
              ) : (
                <>
                  <h3 className="text-xl font-semibold mb-2 text-green-400">Caption</h3>
                  <p className="mb-4">{result.caption}</p>

                  <h4 className="text-lg font-semibold mb-2 text-green-400">Detections</h4>
                  {result.detections && result.detections.length > 0 ? (
                    <ul className="list-disc pl-6 mb-4 max-h-48 overflow-auto">
                      {result.detections.map((d, i) => (
                        <li key={i} className="mb-1">
                          <span className="font-semibold">{d.label}</span> — Confidence:{" "}
                          {d.confidence.toFixed(2)} — bbox: {d.bbox.join(", ")}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No detections</p>
                  )}

                  {result.annotated_image && (
                    <div>
                      <h4 className="text-lg font-semibold mb-2 text-green-400">Annotated</h4>
                      <img
                        src={`data:image/png;base64,${result.annotated_image}`}
                        alt="annotated"
                        className="max-w-full rounded-lg border border-green-600 shadow-lg"
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Summarizer Tab */}
      {activeTab === "summarizer" && (
        <div className="w-full max-w-3xl bg-gray-900 bg-opacity-60 rounded-lg p-6 shadow-lg">
          <h2 className="text-2xl font-semibold mb-4 text-green-300">Document / URL Summarizer</h2>
          <div>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleSumFileChange}
              className="block mb-4 text-gray-300 file:bg-green-700 file:text-white file:px-4 file:py-2 file:rounded cursor-pointer focus:ring-2 focus:ring-green-500"
            />
          </div>
          <div className="mb-4">
            <input
              type="text"
              placeholder="Or paste a URL here"
              value={url}
              onChange={handleUrlChange}
              className="w-full max-w-md rounded-md p-2 bg-gray-800 border border-green-700 text-green-200 placeholder-green-400 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          <button
            onClick={handleSummarize}
            disabled={sumLoading}
            className="px-6 py-2 bg-green-600 rounded-md text-gray-100 font-semibold hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed transition-all shadow-md focus:ring-2 focus:ring-green-400"
          >
            {sumLoading ? "Summarizing..." : "Get Summary"}
          </button>

          {summary && (
            <div className="mt-8 bg-gray-800 p-4 rounded-md border border-green-600 max-w-3xl whitespace-pre-wrap text-green-200 shadow-inner">
              <h3 className="text-xl font-semibold mb-2">Summary</h3>
              <p>{summary}</p>
            </div>
          )}
        </div>
      )}

      {/* Animation style for slow spin */}
      <style>{`
        @keyframes spin-slow {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        .animate-spin-slow {
          animation: spin-slow 120s linear infinite;
        }
      `}</style>
    </div>
  );
}
