This Python script processes images using Microsoft's Azure Vision API to extract text, compares the extracted text with ground truth data, and generates a CSV report with the results. Here's a step-by-step summary of its workflow:
	1.	Configuration and Setup:
	•	Sets up API credentials, directories for images and ground truth data, and an output CSV file.
	•	Implements rate-limiting to adhere to the API's usage limits. 
	2.	Text Extraction from Images:
	•	Reads each image file from the specified directory.
	•	Sends the image to Azure's Vision API for text recognition.
	•	Handles rate limits and retry logic if API limits are exceeded (using 429 Retry-After headers).
	•	Polls the API until the text extraction task is complete.
	3.	Ground Truth Reading:
	•	Matches each image with its corresponding ground truth text file.
	•	Reads the text file and removes spaces to ensure a fair comparison.
	4.	Comparison and Evaluation:
	•	Compares the predicted text from the Vision API with the expected ground truth text.
	•	Marks the result as "correct" or "wrong" based on the comparison.
	5.	Output Generation:
	•	Writes the filename, expected text, predicted text, and correctness ("correct" or "wrong") to the results CSV file.
	•	Logs each processing step and result for user feedback.
	6.	Summary Metrics:
	•	Calculates and displays metrics like total images processed, accuracy, error rate, and processing success rate.
	•	Handles cases where ground truth files are missing.
	7.	Rate Limiting and Error Handling:
	•	Ensures compliance with API rate limits using timers and retries.
	•	Gracefully handles missing ground truth files and API errors.

The output is a CSV file summarizing the results and a detailed summary of performance metrics printed to the console.
