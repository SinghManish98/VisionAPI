import sys
import os
import time
import requests
import csv
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
subscription_key = os.getenv("SUBSCRIPTION_KEY")
endpoint = os.getenv("ENDPOINT")
if not subscription_key or not endpoint:
    raise ValueError("Environment variables 'SUBSCRIPTION_KEY' or 'ENDPOINT' are not set.")
read_url = endpoint + "vision/v3.1/read/analyze"
image_directory = os.path.join(script_dir, "PS1-TR-Data/images")
groundtruth_directory = os.path.join(script_dir, "PS1-TR-Data/groundtruth")
output_csv = os.path.join(script_dir, "results.csv")

# Adjusted API limit
API_CALL_LIMIT = 20  
API_TIME_WINDOW = 60  
CALLS_PER_IMAGE = 2  

# Function to get text using Vision API
def process_image(image_path):
    global api_call_count, start_time

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    headers = {'Ocp-Apim-Subscription-Key': subscription_key,
               'Content-Type': 'application/octet-stream'}
    
    # Enforce rate limit
    current_time = time.time()
    elapsed_time = current_time - start_time
    if api_call_count + CALLS_PER_IMAGE > API_CALL_LIMIT and elapsed_time < API_TIME_WINDOW:
        wait_time = API_TIME_WINDOW - elapsed_time
        print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
        time.sleep(wait_time)
        start_time = time.time()
        api_call_count = 0

    
    while True:
        response = requests.post(read_url, headers=headers, data=image_data)
        if response.status_code == 429:  
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        response.raise_for_status()
        break
    api_call_count += 1

    operation_url = response.headers["Operation-Location"]
    
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        if api_call_count + 1 > API_CALL_LIMIT and elapsed_time < API_TIME_WINDOW:
            wait_time = API_TIME_WINDOW - elapsed_time
            print(f"Rate limit reached while polling. Waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            start_time = time.time()
            api_call_count = 0

        response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key})
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limit exceeded during polling. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        response.raise_for_status()
        api_call_count += 1
        
        analysis = response.json()
        if "status" in analysis and analysis['status'] == 'succeeded':
            break
        time.sleep(1)  
    
    if "analyzeResult" in analysis:
        text = []
        for line in analysis["analyzeResult"]["readResults"][0]["lines"]:
            text.append(line["text"].replace(" ", "")) 
        return "".join(text)  
    else:
        return "No text found in the image."


# Function to read ground truth file
def read_groundtruth(groundtruth_path):
    try:
        with open(groundtruth_path, "r") as gt_file:
            return gt_file.read().strip().replace(" ", "")  
    except FileNotFoundError:
        return None

# Initialize counters and timers
total_images = 0
correct_samples = 0
incorrect_samples = 0
api_call_count = 0
start_time = time.time()

# Prepare the CSV file
with open(output_csv, mode="w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["filename", "expected", "predicted", "correct/wrong"])
    
    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            total_images += 1 
            image_path = os.path.join(image_directory, filename)
            groundtruth_filename = os.path.splitext(filename)[0] + ".txt"
            groundtruth_path = os.path.join(groundtruth_directory, groundtruth_filename)
            
            print(f"Processing {filename}...")

            # Extract text from image (API call)
            predicted_text = process_image(image_path)
            print(f"Predicted Text for {filename}: {predicted_text}")

            # Read ground truth
            expected_text = read_groundtruth(groundtruth_path)
            if expected_text is None:
                print(f"Ground truth file missing for {filename}. Skipping...")
                continue
            
            print(f"Expected Text for {filename}: {expected_text}")

            # Compare and determine correctness
            correctness = "correct" if predicted_text == expected_text else "wrong"
            if correctness == "correct":
                correct_samples += 1
            else:
                incorrect_samples += 1
            
            csv_writer.writerow([filename, expected_text, predicted_text, correctness])
            print(f"Result for {filename}: {correctness}\n")

# Initialize missing ground truth counter
missing_groundtruth = total_images - (correct_samples + incorrect_samples)

# Calculate additional summary metrics
accuracy = (correct_samples / total_images) * 100 if total_images > 0 else 0
error_rate = (incorrect_samples / total_images) * 100 if total_images > 0 else 0
correct_vs_incorrect_ratio = f"{correct_samples}:{incorrect_samples}" if incorrect_samples > 0 else f"{correct_samples}:0"
processed_samples = correct_samples + incorrect_samples
processing_success_rate = (processed_samples / total_images) * 100 if total_images > 0 else 0

# Print detailed summary
print("\nSummary:")
print(f"Total Images Processed: {total_images}")
print(f"Correct Samples: {correct_samples}")
print(f"Incorrect Samples: {incorrect_samples}")
print(f"Accuracy: {accuracy:.2f}%")
print(f"Error Rate: {error_rate:.2f}%")
print(f"Correct vs. Incorrect Ratio: {correct_vs_incorrect_ratio}")
print(f"Missing Ground Truth: {missing_groundtruth}")
print(f"Processing Success Rate: {processing_success_rate:.2f}%")
print(f"Results saved to {output_csv}")
