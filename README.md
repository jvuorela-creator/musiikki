# 🎼 Sukupuu-soitin (GEDCOM to MIDI)

Tämä Python-sovellus muuttaa sukututkimusdatan (GEDCOM-tiedostot) auditiiviseen muotoon. Se luo sukupuusta "aikajanasinfonian", joka auttaa hahmottamaan sukupolvien ketjut ja historian tihentymät äänen avulla.

## Miten se toimii?

Sovellus lukee sukupuutiedoston ja kääntää sen musiikiksi seuraavilla säännöillä:
* **Aika:** Historia etenee lineaarisesti.
* **Ääni:** Henkilön syntymä aloittaa nuotin, kuolema lopettaa sen.
* **Sävelkorkeus:** Määräytyy syntymävuoden mukaan. Vanhimmat sukupolvet ovat matalia bassoääniä, nykypäivän sukupolvet korkeita ääniä.
* **Intensiteetti:** Mitä enemmän sukulaisia on elossa yhtä aikaa, sitä "tiheämpi" musiikki.

## Käyttöohjeet

### Vaihtoehto A: Käyttö selaimessa (Streamlit Cloud)
Jos sovellus on asennettu pilveen, avaa vain linkki, raahaa `.ged`-tiedostosi ruutuun ja lataa syntynyt MIDI-tiedosto.

### Vaihtoehto B: Paikallinen asennus
Jos haluat ajaa koodia omalla koneellasi:

1. Asenna tarvittavat kirjastot:
   ```bash
   pip install -r requirements.txt
