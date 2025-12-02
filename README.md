# Molecular_Data_Explorer

Interactive Streamlit app to search, visualize and compare chemical compounds using PubChem APIs and 3D rendering (py3Dmol).

## Features
- Autocomplete search (PubChem)
- Real-time molecular data fetch
- 3D molecule rendering using py3Dmol (SDF from PubChem)
- Chemical safety information
- Side-by-side compound comparison
- Molecular property charts (Altair)
- AI-like similar compound suggestions

## Minimal Requirements
streamlit
requests
py3Dmol
pandas
altair

## Notes
Py3Dmol rendering requires a modern browser with WebGL enabled.
PubChem request limits are generous but avoid hammering the API in loops.

