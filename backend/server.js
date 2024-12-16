// server.js
const { spawn } = require('child_process');

const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;

// Use CORS middleware to allow cross-origin requests
app.use(cors());

// Include middleware to parse JSON bodies
app.use(express.json());

// Define a POST route to receive the data
app.post('/submit', (req, res) => {

  console.log(req.body);
  const data = JSON.stringify(req.body, 2);
  
  const python = spawn('python', ['model.py']);         //`python model.py ${data.replace(/"/g, '\\""')}"`;

  let output = '';
  let errorOutput = '';  

  // Collect data from Python script
  python.stdout.on('data', (data) => {
    output += data.toString();
  });

  python.stderr.on('data', (data) => {
    errorOutput += data.toString();
  });

  python.on('close', (code) => {
    if (code === 0) {
      // Send the Python script's output back to the client
      console.log(output);
      res.send(output);
    } else {
      console.error(`Python script exited with code ${code}`);
      console.error(`Error output: ${errorOutput}`);
      res.status(500).send(errorOutput);
    }
  });

  // Send the JSON data to the Python script via stdin
  python.stdin.write(data);
  python.stdin.end();
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
