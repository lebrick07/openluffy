// Sample Node.js Express Application
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: process.env.SERVICE_NAME || 'api' });
});

// Sample API endpoint
app.get('/api/hello', (req, res) => {
  res.json({ message: 'Hello from your OpenLuffy-powered application!' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

module.exports = app;
