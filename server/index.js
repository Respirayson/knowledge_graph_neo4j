import express from "express";
import * as dotenv from "dotenv";
import cors from "cors";
import { GoogleGenerativeAI } from "@google/generative-ai";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({
  model: "gemini-1.5-flash",
  generationConfig: { response_mime_type: "application/json" },
});

function convertToJSONFile(inputText) {
    // Extract the JSON part from the input text
    const startIndex = inputText.indexOf('{');
    const endIndex = inputText.lastIndexOf('}') + 1;
    const jsonStr = inputText.slice(startIndex, endIndex);

    // Parse the JSON string to ensure it's valid JSON
    return jsonStr;
}

app.get("/", (req, res) => {
  res.send("Hello World!");
});

app.post("/", async (req, res) => {
  const chat = model.startChat({ history: []});

  await chat.sendMessage(req.body.prompt);

  const result = await chat.sendMessage(req.body.data);  

  const response = await result.response;
  const text = response.text();
  console.log(text);
  res.json(text);
});

const start = async () => {
  app.listen(process.env.PORT, () => {
    console.log(`Listening on port ${process.env.PORT}`);
  });
};

start();
