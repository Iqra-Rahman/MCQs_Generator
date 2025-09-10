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

const App = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [numMcqs, setNumMcqs] = useState(100);
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

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        PDF MCQ Generator
      </Typography>

      <Box sx={{ mb: 2 }}>
        <input type="file" accept=".pdf" onChange={handleFileChange} />
      </Box>

      <TextField
        label="Number of MCQs"
        type="number"
        value={numMcqs}
        onChange={(e) => setNumMcqs(parseInt(e.target.value) || 100)}
        fullWidth
        sx={{ mb: 2 }}
      />

      <Button variant="contained" onClick={handleSubmit} disabled={loading}>
        Generate
      </Button>

      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
      {loading && <CircularProgress sx={{ mt: 2 }} />}

      {keywords.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6">Extracted Keywords:</Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {keywords.map((kw, idx) => (
              <Chip key={idx} label={kw} variant="outlined" />
            ))}
          </Box>
        </Box>
      )}

      {mcqs.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6">Generated MCQs:</Typography>
          <List>
            {mcqs.map((mcq, idx) => (
              <React.Fragment key={idx}>
                <ListItem>
                  <ListItemText
                    primary={`${idx + 1}. ${mcq.question}`}
                    secondary={
                      <>
                        A: {mcq.options?.A}<br />
                        B: {mcq.options?.B}<br />
                        C: {mcq.options?.C}<br />
                        D: {mcq.options?.D}<br />
                        <strong>Correct: {mcq.correct_answer}</strong><br />
                        Explanation: {mcq.explanation}<br />
                        Difficulty: {mcq.difficulty}
                      </>
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
