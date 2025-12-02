import streamlit as st
import requests
import py3Dmol
import pandas as pd
import altair as alt

st.set_page_config(page_title="Molecular Data Explorer", layout="wide")
st.title("🔬 Molecular Data Explorer")

# --- Autocomplete Suggestions ---
def get_suggestions(query):
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/{query}/json"
        res = requests.get(url)
        return res.json().get("dictionary", {}).get("compound", [])
    except:
        return []

# --- Fetch compound data ---
def fetch_pubchem_data(compound_name):
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/property/MolecularFormula,MolecularWeight,CanonicalSMILES,InChIKey,Title,XLogP,HBondDonorCount,HBondAcceptorCount/JSON"
        res = requests.get(url)
        data = res.json()
        return data["PropertyTable"]["Properties"][0]
    except:
        return None

# --- Fetch compound CID and safety info ---
def fetch_safety_info(compound_name):
    try:
        cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/cids/JSON"
        cid = requests.get(cid_url).json()["IdentifierList"]["CID"][0]
        safety_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
        safety_data = requests.get(safety_url).json()

        for section in safety_data.get("Record", {}).get("Section", []):
            if section.get("TOCHeading", "") == "Safety and Hazards":
                info = section.get("Information", [])
                if info:
                    value = info[0].get("Value", {}).get("StringWithMarkup", [])
                    if value:
                        return value[0].get("String", "No safety data available.")
        return "No safety data available."
    except:
        return "No safety data available."

# --- Suggest similar compounds ---
def suggest_similar(compound_data):
    try:
        weight = compound_data.get("MolecularWeight", 0)
        lower = max(0, weight - 10)
        upper = weight + 10
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/property/MolecularWeight,Title/JSON?MolecularWeight={lower}-{upper}"
        res = requests.get(url).json()
        props = res["PropertyTable"]["Properties"]
        titles = list({item["Title"] for item in props if item.get("Title","").lower() != compound_data.get("Title", "").lower()})
        return titles[:5]
    except:
        return []

# --- Render 3D Model from CID using SDF ---
def render_3d(compound_name):
    try:
        # Get CID from name
        cid_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound_name}/cids/JSON"
        cid = requests.get(cid_url).json()["IdentifierList"]["CID"][0]

        # Get 3D structure as SDF (record_type=3d)
        sdf_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/record/SDF/?record_type=3d"
        sdf_data = requests.get(sdf_url).text

        # Render with py3Dmol
        mol_view = py3Dmol.view(width=400, height=400)
        mol_view.addModel(sdf_data, 'sdf')
        mol_view.setStyle({'stick': {}})
        mol_view.zoomTo()
        mol_view.spin(True)
        return mol_view._make_html()
    except Exception as e:
        # helpful fallback for debugging
        return f"<div style='color:red;'>3D structure not available for this compound.<br><small>{str(e)}</small></div>"

# --- Search Inputs ---
colA, colB = st.columns(2)

with colA:
    search1 = st.text_input("🔍 Compound 1")
    suggestions1 = get_suggestions(search1) if search1 else []
    compound1 = st.selectbox("Suggestions for Compound 1", suggestions1) if suggestions1 else search1

with colB:
    search2 = st.text_input("🔍 Compound 2 (Optional for comparison)")
    suggestions2 = get_suggestions(search2) if search2 else []
    compound2 = st.selectbox("Suggestions for Compound 2", suggestions2) if suggestions2 else search2

# --- Display Compound Info ---
def display_info(compound, label):
    data = fetch_pubchem_data(compound)
    if not data:
        st.error(f"{label} not found.")
        return

    st.markdown(f"### 📘 {label}: {compound.capitalize()}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**🧪 Molecular Formula:** {data.get('MolecularFormula', 'N/A')}")
        st.write(f"**⚖️ Molecular Weight:** {data.get('MolecularWeight', 'N/A')} g/mol")
        st.write(f"**🔗 Canonical SMILES:** {data.get('CanonicalSMILES', 'N/A')}")
        st.write(f"**🧬 InChIKey:** {data.get('InChIKey', 'N/A')}")
        st.write(f"**💧 XLogP:** {data.get('XLogP', 'N/A')}")
        st.write(f"**🫁 H-Bond Donors:** {data.get('HBondDonorCount', 'N/A')}")
        st.write(f"**🫀 H-Bond Acceptors:** {data.get('HBondAcceptorCount', 'N/A')}")

        st.markdown("#### 🤖 Similar Compounds")
        similar = suggest_similar(data)
        st.write(", ".join(similar) if similar else "No similar compounds found.")

        st.markdown("#### ⚠️ Safety Info")
        st.info(fetch_safety_info(compound))

        # Chart
        st.markdown("#### 📊 Properties Chart")
        df = pd.DataFrame({
            "Property": ["Molecular Weight", "XLogP", "H-Bond Donors", "H-Bond Acceptors"],
            "Value": [
                float(data.get('MolecularWeight', 0) or 0),
                float(data.get('XLogP', 0) or 0),
                int(data.get('HBondDonorCount', 0) or 0),
                int(data.get('HBondAcceptorCount', 0) or 0)
            ]
        })
        chart = alt.Chart(df).mark_bar().encode(
            x='Property',
            y='Value',
            color='Property'
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

    with col2:
        st.markdown("#### 🔬 3D Structure")
        html = render_3d(compound)
        st.components.v1.html(html, height=420, width=400)


# --- Show Results ---
if compound1:
    st.divider()
    display_info(compound1, "Compound 1")

if compound2:
    st.divider()
    display_info(compound2, "Compound 2")
