import streamlit as st
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import re
import tempfile
import os
import io

# --- Aputoiminnot ---
def parse_year(date_str):
    """Etsii vuosiluvun GEDCOM-päivämäärästä."""
    if not date_str:
        return None
    match = re.search(r'\d{4}', date_str)
    if match:
        return int(match.group(0))
    return None

def create_midi(gedcom_path, tempo_val, year_duration, output_filename="family_tree.mid"):
    """Lukee GEDCOMin ja luo MIDI-tiedoston parametrien mukaan."""
    
    # 1. Luetaan GEDCOM
    gedcom = Parser()
    gedcom.parse_file(gedcom_path)
    root_elements = gedcom.get_root_child_elements()
    
    people = []
    min_year = 3000
    max_year = 0
    
    # Parametrit
    MIN_NOTE = 36  # C2
    MAX_NOTE = 90  # Skaalataan hieman alemmas jotta ei mene liian kimeäksi
    
    for element in root_elements:
        if isinstance(element, IndividualElement):
            birth_data = element.get_birth_data()
            death_data = element.get_death_data()
            
            birth_year = parse_year(birth_data[0]) if birth_data else None
            death_year = parse_year(death_data[0]) if death_data else None
            
            if birth_year:
                if not death_year:
                    death_year = 2025 # Oletetaan eläväksi
                
                if death_year < birth_year:
                    continue

                full_name = " ".join(element.get_name())
                people.append({
                    "start": birth_year,
                    "end": death_year,
                    "name": full_name
                })
                
                if birth_year < min_year: min_year = birth_year
                if death_year > max_year: max_year = death_year

    if not people:
        return None, "Ei löytynyt henkilöitä, joilla on syntymävuosi."

    # 2. Luodaan MIDI
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    
    # Asetetaan tempo (käyttäjän valinta)
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_val)))
    
    # Instrumentti: Celesta (tuntuu "aavemaiselta" ja historialliselta)
    # 0=Piano, 8=Celesta, 40=Viulu, 73=Huilu
    track.append(Message('program_change', program=8))

    events = []
    year_range = max_year - min_year if max_year > min_year else 1
    
    for p in people:
        # Lasketaan nuotin korkeus iän mukaan (vanhat matalalla, nuoret korkealla)
        normalized_pos = (p['start'] - min_year) / year_range
        pitch = int(MIN_NOTE + (normalized_pos * (MAX_NOTE - MIN_NOTE)))
        pitch = max(0, min(127, pitch))

        # Note ON
        events.append({
            "type": "note_on",
            "time_year": p['start'],
            "note": pitch,
            "velocity": 64
        })
        # Note OFF
        events.append({
            "type": "note_off",
            "time_year": p['end'],
            "note": pitch,
            "velocity": 0
        })

    events.sort(key=lambda x: x['time_year'])
    
    previous_year = min_year
    for event in events:
        delta_years = event['time_year'] - previous_year
        # Käyttäjän valitsema nopeus (ticks per year)
        delta_ticks = int(delta_years * year_duration)
        
        track.append(Message(event['type'], note=event['note'], velocity=event['velocity'], time=delta_ticks))
        previous_year = event['time_year']
        
    # Tallennetaan muistiin (BytesIO) jotta Streamlit voi ladata sen
    midi_buffer = io.BytesIO()
    mid.save(file=midi_buffer)
    midi_buffer.seek(0)
    
    return midi_buffer, f"Käsitelty {len(people)} henkilöä vuosilta {min_year}-{max_year}."

# --- Streamlit Käyttöliittymä ---

st.title("🎼 Sukupuun Sonifikaatio")
st.markdown("""
Tämä sovellus muuttaa GEDCOM-sukupuutiedoston musiikiksi.
- **Syntymä** aloittaa äänen.
- **Kuolema** lopettaa äänen.
- **Sävelkorkeus** nousee, mitä lähemmäs nykypäivää tullaan.
""")

# 1. Tiedoston lataus
uploaded_file = st.file_uploader("Lataa GEDCOM-tiedosto (.ged)", type=["ged"])

# 2. Asetukset
col1, col2 = st.columns(2)
with col1:
    bpm = st.slider("Tempo (BPM)", 60, 240, 120, help="Kuinka nopea perussyke on.")
with col2:
    year_dur = st.slider("Vuoden pituus (kesto)", 10, 500, 100, help="Pieni luku = historia vilahtaa ohi. Suuri luku = hidas eteneminen.")

# 3. Prosessointi
if uploaded_file is not None:
    st.write("---")
    st.info("Tiedosto ladattu. Prosessoidaan...")
    
    # Gedcom-parser vaatii oikean tiedostopolun, joten tallennetaan väliaikaistiedosto
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ged") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Ajetaan muunnosfunktio
        midi_data, msg = create_midi(tmp_path, bpm, year_dur)
        
        if midi_data:
            st.success("Valmis! " + msg)
            
            # Latausnappi
            st.download_button(
                label="🎵 Lataa MIDI-tiedosto",
                data=midi_data,
                file_name="sukupuu_musiikki.mid",
                mime="audio/midi"
            )
            st.warning("**Huom:** Selaimet eivät soita MIDI-tiedostoja. Lataa tiedosto ja avaa se koneesi mediasoittimella (esim. Windows Media Player, VLC tai GarageBand).")
            
        else:
            st.error(msg)
            
    except Exception as e:
        st.error(f"Tapahtui virhe tiedoston käsittelyssä: {e}")
        
    finally:
        # Siivotaan väliaikaistiedosto pois
        os.remove(tmp_path)