# Audio Metadata Generator with YAMNet

## Overview

For sample listing, we process the audio files to generate rich metadata, including:
- **Key and BPM (Beats Per Minute)**.
- **Energy, Dynamics, and Brightness**.
- **Sound Classifications** using **YAMNet** (a pre-trained audio classification model).
- A descriptive **vibe** for each track.

The metadata is saved in both **JSON** and **CSV** formats, making it easy to integrate into other workflows.

---

## Features
1. **Audio Analysis**:
    - Detects key (e.g., G major, A minor).
    - Computes tempo, energy levels, and spectral brightness.
    - Analyzes dynamic range and tonality.

2. **Sound Classification with YAMNet**:
    - Identifies the top 5 sound categories from over 500 predefined classes (e.g., "Electric Guitar," "Drums").
    - Includes these classifications in the metadata tags.

3. **Metadata Output**:
    - **JSON**: Structured data for programmatic use.
    - **CSV**: Tabular format for manual inspection or integration with other tools.

---

## How It Works

### 1. Audio Processing
The sample listing script analyzes each audio file to extract:
- **Key**: Identifies the musical key (e.g., G major).
- **Tempo (BPM)**: Calculates the beats per minute and categorizes tempo as Relaxed, Moderate, or Energetic.
- **Energy and Brightness**: Determines whether the track is high-energy or low-energy and bright or warm.
- **Dynamic Range**: Assesses whether the sound is soft or intense.

### 2. YAMNet Sound Classification
- The script uses **YAMNet**, a TensorFlow-based model trained on Google’s AudioSet, to classify the audio.
- The top 5 categories with the highest confidence are included in the metadata tags.

### 3. Metadata Generation
For each file, the script generates:
- **Vibe**: A descriptive summary of the track’s energy, brightness, key, tempo, and dynamics.
- **Tags**: A list of attributes, including tempo category, energy level, key, and YAMNet classifications.

---

## Requirements

### Python Packages
Install the required packages using `pip`:
```bash
pip install tensorflow librosa numpy
