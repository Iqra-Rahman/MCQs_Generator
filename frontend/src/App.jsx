import React, { useState } from "react";
import axios from "axios";
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
} from "@mui/material";
import "./app.css";

const App = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [numMcqs, setNumMcqs] = useState(10);
  const [loading, setLoading] = useState(false);
  const [mcqs, setMcqs] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setPdfFile(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    if (!pdfFile) {
      setError("Please upload a PDF file.");
      return;
    }
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", pdfFile);
    formData.append("num_mcqs", numMcqs.toString());

    try {
      const response = await axios.post("http://localhost:8000/generate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMcqs(response.data.mcqs || []);
      setKeywords(response.data.keywords || []);
    } catch (err) {
      setError("Error generating questions. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Function to download MCQs as a text file
  const handleDownload = () => {
    if (mcqs.length === 0) return;

    const content = mcqs
      .map(
        (mcq, idx) =>
          `${idx + 1}. ${mcq.question}\nA) ${mcq.options?.A}\nB) ${
            mcq.options?.B
          }\nC) ${mcq.options?.C}\nD) ${mcq.options?.D}\nCorrect Answer: ${
            mcq.correct_answer
          }\nExplanation: ${mcq.explanation}\nDifficulty: ${
            mcq.difficulty
          }\n\n`
      )
      .join("");

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "generated_mcqs.txt";
    a.click();

    URL.revokeObjectURL(url);
  };

  return (
    <Container maxWidth="md" className="glass-container">
      <Typography variant="h3" className="app-title">
         AI-Powered PDF MCQ Generator 
      </Typography>

      <Box className="upload-box">
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="file-input"
        />
      </Box>

      <TextField
        label="Number of MCQs"
        type="number"
        value={numMcqs}
        onChange={(e) => setNumMcqs(parseInt(e.target.value) || 100)}
        fullWidth
        className="text-field"
      />

      <Button
        variant="contained"
        className="generate-btn"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading ? "Generating..." : "Generate MCQs"}
      </Button>

      {error && <Typography color="error" className="error-text">{error}</Typography>}
      {loading && <CircularProgress className="loader" />}

      {keywords.length > 0 && (
        <Box className="keywords-section">
          <Typography variant="h5" className="section-title">
            Extracted Keywords
          </Typography>
          <Box className="keywords-box">
            {keywords.map((kw, idx) => (
              <Chip key={idx} label={kw} className="keyword-chip" />
            ))}
          </Box>
        </Box>
      )}
      {/*  Download Button */}
          <Button
        variant="contained"
        className="generate-btn"
        onClick={handleDownload}
        disabled={mcqs.length === 0}
        style={{
          marginTop: "15px",
          background: "#545454",
          opacity: mcqs.length === 0 ? 0.5 : 1,
          pointerEvents: mcqs.length === 0 ? "none" : "auto",
        }}
      >
            Download Generated MCQs
          </Button>

      {mcqs.length > 0 && (
        <Box className="mcq-section">
          <Typography variant="h5" className="section-title">
            Generated MCQs
          </Typography>
          <List className="mcq-list">
            {mcqs.map((mcq, idx) => (
              <React.Fragment key={idx}>
                <ListItem className="mcq-item">
                  <ListItemText
                    primary={`${idx + 1}. ${mcq.question}`}
                    secondary={
                      <div className="mcq-options">
                        <p>A: {mcq.options?.A}</p>
                        <p>B: {mcq.options?.B}</p>
                        <p>C: {mcq.options?.C}</p>
                        <p>D: {mcq.options?.D}</p>
                        <strong>Correct: {mcq.correct_answer}</strong><br />
                        <span>Explanation: {mcq.explanation}</span><br />
                        {/* <span>Difficulty: {mcq.difficulty}</span> */}
                      </div>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
          
        </Box>
      )}
    </Container>
  );
};

export default App;
