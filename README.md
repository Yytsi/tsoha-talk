# tsoha-talk 🗣️😊
Tietokannat ja web-ohjelmointi kurssille viestittelysovellus.

Pidän kurssisivustolla esitetystä keskustelusovellusideasta: "Sovelluksessa näkyy keskustelualueita, joista jokaisella on tietty aihe. Alueilla on keskusteluketjuja, jotka muodostuvat viesteistä. Jokainen käyttäjä on peruskäyttäjä tai ylläpitäjä." Ohjelmani on ymmärtääkseni muunnelma yllä olevasta kuvauksesta.

Tässä tarkemmin ominaisuudet (otettu materiaalista):

- Käyttäjä voi kirjautua sisään ja ulos sekä luoda uuden tunnuksen. ✅
- Käyttäjä näkee sovelluksen etusivulla listan foorumeista sekä jokaisen foorumin sisältämän ketjun viestien määrän ja viimeksi lähetetyn viestin ajankohdan. ✅
- Käyttäjä voi luoda foorumiin uuden ketjun antamalla ketjun otsikon ja aloitusviestin sisällön. ✅
- Käyttäjä voi kirjoittaa uuden viestin olemassa olevaan ketjuun. ✅
- Käyttäjä voi muokata luomansa ketjun otsikkoa sekä lähettämänsä viestin sisältöä. Käyttäjä voi myös poistaa ketjun tai viestin. ⌛
- Käyttäjä voi etsiä kaikki viestit, joiden osana on annettu sana. ⌛
- Ylläpitäjä voi lisätä ja poistaa ketjuja sekä foorumeita. ⌛
- Ylläpitäjä voi luoda salaisen foorumin ja määrittää, keillä käyttäjillä on pääsy alueelle. ⌛


Tässä ohjeet käynnistämiseen (tarvitset Pythonin).

1. `pip install -r requirements.txt`
2. `source env/bin/activate`
3. Aseta .env tiedostoon 2 riviä, alla olevan kuvan mukaisesti. Vaihda secret key  ja tietokannan osoite sopiviksi.
4. Suorita `flask run` projektin juuressa.
5. Avaa ohjelma flaskin kertomasta osoitteesta.

<img width="657" alt="image" src="https://github.com/user-attachments/assets/0a6a79bd-9497-4c3a-8b20-aceaa6d45fe1">


## Välipalautus 2

Sovelluksen perusominaisuuksia on toteutettu, mutta ulkonäkö on karkea. Seuraavaan välipalautukseen mennessä sovelluksella on kauniimpi ulkoasu sekä enemmän toteutettuja ominaisuuksia.
