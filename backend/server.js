// server.js
const { spawn } = require('child_process');
const crypto = require('crypto'); // For generating random suffix
const path = require('path');
const fs = require('fs');
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

  // console.log(req.body);
  const data = JSON.stringify(req.body, 2);
  
  const python = spawn('python', ['model.py']);

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
      // console.log(output);
      res.send(output);
    } else {
      console.error(`Python script exited with code ${code}`);
      console.error(`Error output: ${errorOutput}`);

      // Create logs folder
      const logsFolder = path.join(__dirname, 'logs');
      if (!fs.existsSync(logsFolder)) {
        fs.mkdirSync(logsFolder);
      }

      // Generate filename with current datetime
      const timestamp = new Date().toISOString().replace(/:/g, '-');
      let logFilename = `log-${timestamp}.log`;
      let logFilePath = path.join(logsFolder, logFilename);

      // Check if file already exists, and add random suffix if needed
      while (fs.existsSync(logFilePath)) {
        const randomSuffix = crypto.randomBytes(4).toString('hex');
        logFilename = `log-${timestamp}-${randomSuffix}.log`;
        logFilePath = path.join(logsFolder, logFilename);
      }

      // Write error output to the log file
      fs.writeFileSync(logFilePath, `Error code: ${code}\nError output:\n${errorOutput}\nData:\n${data}`);
      console.log(logFilePath);
      // Respond to the client with an error message
      res.status(500).send(`An error occurred. Details logged in ${logFilename}`);
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
