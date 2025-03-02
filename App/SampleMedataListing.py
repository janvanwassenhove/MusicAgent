import os
import json
import csv
import librosa
import tensorflow as tf
import numpy as np
import faiss
import logging
import time
from sentence_transformers import SentenceTransformer

# Configure logging
log_file = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(log_file, 'a', 'utf-8')])
logger = logging.getLogger(__name__)

progress_file = os.path.join(os.path.dirname(__file__), 'progress.json')

def update_progress(progress):
    with open(progress_file, 'w') as f:
        json.dump({"progress": progress}, f)

# Load YAMNet model and class names
yamnet_model = tf.saved_model.load("inc/yamnet-tensorflow2-yamnet-v1")  # Load the model from the specified directory
yamnet_classes = []
with open("Inc/yamnet-tensorflow2-yamnet-v1/assets/yamnet_class_map.csv", "r") as f:
    yamnet_classes = [line.strip() for line in f.readlines()]

def preprocess_audio(file_path):
    """Preprocess the audio for YAMNet: mono and 16kHz sampling rate."""
    try:
        y, sr = librosa.load(file_path, sr=16000, mono=True)  # Resample to 16kHz
        return tf.convert_to_tensor(y, dtype=tf.float32)
    except Exception as e:
        raise ValueError(f"Error preprocessing audio file {file_path}: {e}")

def classify_sound(file_path):
    """Classify audio sound using YAMNet and clean up tags."""
    try:
        waveform = preprocess_audio(file_path)

        # Get prediction scores
        scores, embeddings, spectrogram = yamnet_model(waveform)

        # Get the top 5 classes with highest scores
        top_5_indices = tf.argsort(scores[0], direction="DESCENDING")[:5].numpy()
        top_5_classes = [
            (yamnet_classes[i].split(",")[-1].strip().replace('"', ''), float(scores[0][i].numpy()))
            for i in top_5_indices
        ]

        return top_5_classes
    except Exception as e:
        return [("Error", 0.0)]

def detect_key(y, sr):
    """Detect the musical key (e.g., C major, A minor) of the audio."""
    try:
        # Calculate chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=12, hop_length=512)
        chroma_mean = chroma.mean(axis=1)

        # Skip if chroma_mean has all zeros
        if np.max(chroma_mean) == 0:
            return "Unknown"

        # Normalize chroma features
        chroma_mean /= np.max(chroma_mean)

        # Major and Minor templates
        major_template = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
        minor_template = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])

        # Correlate with templates
        major_scores = [np.correlate(chroma_mean, np.roll(major_template, i))[0] for i in range(12)]
        minor_scores = [np.correlate(chroma_mean, np.roll(minor_template, i))[0] for i in range(12)]

        # Determine best match
        best_major = np.argmax(major_scores)
        best_minor = np.argmax(minor_scores)

        if major_scores[best_major] > minor_scores[best_minor]:
            mode = "major"
            key_index = best_major
        else:
            mode = "minor"
            key_index = best_minor

        # Key names
        key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return f"{key_names[key_index]} {mode}"
    except Exception as e:
        print(f"Error detecting key: {e}")
        return "Unknown"

def process_audio(file_path):
    """Extract key, BPM, duration, vibe, track type, and detailed description from an audio file."""
    try:
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)

        # Skip very short audio files
        if duration < 0.8:
            return {"Filename": file_path.replace("\\", "/"), "Error": "Audio too short to analyze"}

        n_fft = min(1024, len(y))

        # Extract BPM and ensure it's a scalar
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(tempo, np.ndarray):  # Check if tempo is an array
            tempo = tempo[0] if tempo.size > 0 else 0
        tempo = float(tempo)

        tempo_category = (
            "Relaxed" if tempo < 90 else
            "Moderate" if 90 <= tempo < 120 else
            "Energetic"
        )

        # Spectral features
        spectral = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft)
        brightness = "bright" if spectral.mean() > 2000 else "warm"

        # RMS Energy
        rms = librosa.feature.rms(y=y, frame_length=n_fft).mean()

        # Adjust the energy threshold dynamically or lower it
        energy_threshold = 0.005  # Lowered threshold for low-energy files
        if rms < energy_threshold:
            print(f"Warning: Audio file '{file_path}' has very low energy (RMS = {rms:.6f}). Proceeding with caution.")
            energy = "very low energy"
        else:
            energy = "high energy" if rms > 0.05 else "low energy"

        max_amplitude = np.max(np.abs(y))
        dynamic_range = "intense and punchy" if max_amplitude > 0.8 else "soft and smooth"

        key = detect_key(y, sr)

        top_5_classes = classify_sound(file_path)
        classification_tags = [cls[0] for cls in top_5_classes]

        # Expanded instrumental categories
        instrumental_categories = {
            "Piano", "Electric Guitar", "Drums", "Bass Guitar", "Flute", "Violin",
            "Harmonica", "Synthesizer", "Trumpet", "Saxophone", "Acoustic Guitar", "Strings"
        }
        vocal_categories = {"Singing", "Choir", "Speech", "Vocal", "Opera", "Rap"}

        contains_vocals = any(tag in vocal_categories for tag in classification_tags)
        contains_instrumentals = any(tag in instrumental_categories for tag in classification_tags)

        track_type = "Unknown"
        if contains_vocals and contains_instrumentals:
            track_type = "Both Vocals and Instrumentals"
        elif contains_vocals:
            track_type = "Vocals Only"
        elif contains_instrumentals:
            track_type = "Instrumentals Only"

        vibe_description = (
            f"The track has a {tempo_category} tempo at {round(tempo)} BPM, "
            f"featuring a {brightness} and {energy} sound. It feels {dynamic_range} "
            f"with a {key} tonality."
        )

        tags = [tempo_category, brightness, energy, dynamic_range, key] + classification_tags
        tags = [tag for tag in tags if tag != "Unknown"]

        parent_folder = os.path.basename(os.path.dirname(file_path))
        filename = os.path.basename(file_path)
        result = {
            "Filename": f"{parent_folder}/{filename}",
            "Duration": round(duration, 2),
            "BPM": round(tempo, 2),
            "Key": key,
            "Vibe": vibe_description,
            "Tags": tags,
            "Description": f"A {brightness}, {energy} track with a {tempo_category} tempo and a {key} tonality.",
        }

        if track_type != "Unknown": #don't add if unknown to gain tokens
            result["Track Type"] = track_type

        return result
    except Exception as e:
        return {"Filename": file_path.replace("\\", "/"), "Error": str(e)}

def process_subfolder(subfolder_path):
    """Process all audio files in a subfolder and save metadata to JSON and CSV files."""
    metadata_list = []

    for root, _, files in os.walk(subfolder_path):
        for file in files:
            if file.endswith(('.mp3', '.wav', '.flac')):  # Supported formats
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")  # Debug log
                metadata = process_audio(file_path)
                if "Error" not in metadata:
                    metadata_list.append(metadata)
                else:
                    print(f"Error processing file {file_path}: {metadata['Error']}")

    if not metadata_list:
        print(f"No valid audio files found in the subfolder: {subfolder_path}")
        return None

    subfolder_name = os.path.basename(subfolder_path)
    json_output = os.path.join(subfolder_path, f"{subfolder_name}_metadata.json")
    csv_output = os.path.join(subfolder_path, f"{subfolder_name}_metadata.csv")

    save_to_json(metadata_list, json_output)
    return json_output

def save_to_json(metadata_list, output_file):
    """Save metadata to a JSON file."""
    if not metadata_list:
        logger.info(f"No metadata to save. Skipping JSON creation.")
        return
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(metadata_list, json_file, indent=4)
    logger.info(f"Metadata saved to JSON: {output_file}")

def process_directory(input_directory):
    """Process each subfolder in the directory and create a summary JSON file."""
    logger.info(f"Processing directory: {input_directory}")
    update_progress(0)
    summary = []

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = []
    metadata = []

    total_subfolders = len(next(os.walk(input_directory))[1])
    processed_subfolders = 0

    for root, dirs, _ in os.walk(input_directory):
        for subfolder in dirs:
            subfolder_path = os.path.join(root, subfolder)
            logger.info(f"Processing subfolder: {subfolder_path}")
            json_output = process_subfolder(subfolder_path)
            if json_output:
                summary.append({
                    "subfolder": subfolder,
                    "file_location": json_output.replace("\\", "/")
                })
                with open(json_output, 'r', encoding='utf-8') as f:
                    json_content = json.load(f)

                for item in json_content:
                    metadata.append(item)
                processed_subfolders += 1
                progress = (processed_subfolders / total_subfolders) * 90
                update_progress(progress)
                print(f"Progress: {progress:.2f}%")

    print("Progress: 90.00%")

    final_json_content = json.dumps(metadata)  # Serialize the entire metadata array
    embedding = model.encode(final_json_content)  # Encode the final JSON string
    embeddings.append(embedding)  # Append the embedding

    try:
        summary_json = os.path.join(input_directory, "summary_samples.json")
        with open(summary_json, "w", encoding="utf-8") as json_file:
            json.dump(summary, json_file, indent=4)
        logger.info(f"Summary JSON saved: {summary_json}")
    except Exception as e:
        logger.error(f"Failed to save summary JSON: {e}")
        if not os.path.exists(summary_json):
            with open(summary_json, "w", encoding="utf-8") as json_file:
                json.dump([], json_file, indent=4)
        logger.info(f"Created empty summary JSON: {summary_json}")

    # Convert embeddings to a NumPy array
    embedding_array = np.array(embeddings).astype("float32")

    # Create a FAISS index
    dimension = embedding_array.shape[1]  # Embedding size
    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_array)

    # Save the index and metadata
    faiss.write_index(index, os.path.join(input_directory, "sample_index.faiss"))
    with open(os.path.join(input_directory, "sample_metadata.json"), "w") as f:
        json.dump(metadata, f)

    logger.info("Processing complete")
    update_progress(100)

# Main script
if __name__ == "__main__":
    input_directory = os.path.join(os.path.dirname(__file__), "..", "Samples")

    process_directory(input_directory)

    # Load summary_samples.json
    summary_json_path = os.path.join(input_directory, "summary_samples.json")
    with open(summary_json_path, 'r', encoding='utf-8') as f:
        summary_samples = json.load(f)

    # agent_config_directory = 'AgentConfig'
    # file_locations = ["audio_metadata.json"]  # Example file locations
    # update_assistants_in_song_config(agent_config_directory)