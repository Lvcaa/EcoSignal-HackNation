"""Italian ZIP code to coordinates and ARPA region mapping.

Covers all 20 Italian regions with at least one major city each.
Coordinates are realistic city-center values.
"""

from __future__ import annotations

from app.schemas import ZipLocation

# ---------------------------------------------------------------------------
# ZIP -> ZipLocation lookup table
# ---------------------------------------------------------------------------

ZIP_COORDINATE_MAP: dict[str, ZipLocation] = {
    # --- Lazio ---
    "00100": ZipLocation(
        zip_code="00100", city="Roma", region="Lazio",
        latitude=41.9028, longitude=12.4964, arpa_region="ARPA_LAZIO",
    ),
    # --- Lombardia ---
    "20100": ZipLocation(
        zip_code="20100", city="Milano", region="Lombardia",
        latitude=45.4642, longitude=9.1900, arpa_region="ARPA_LOMBARDIA",
    ),
    "25100": ZipLocation(
        zip_code="25100", city="Brescia", region="Lombardia",
        latitude=45.5416, longitude=10.2118, arpa_region="ARPA_LOMBARDIA",
    ),
    "24100": ZipLocation(
        zip_code="24100", city="Bergamo", region="Lombardia",
        latitude=45.6983, longitude=9.6773, arpa_region="ARPA_LOMBARDIA",
    ),
    # --- Campania ---
    "80100": ZipLocation(
        zip_code="80100", city="Napoli", region="Campania",
        latitude=40.8518, longitude=14.2681, arpa_region="ARPA_CAMPANIA",
    ),
    "84100": ZipLocation(
        zip_code="84100", city="Salerno", region="Campania",
        latitude=40.6824, longitude=14.7681, arpa_region="ARPA_CAMPANIA",
    ),
    # --- Sicilia ---
    "90100": ZipLocation(
        zip_code="90100", city="Palermo", region="Sicilia",
        latitude=38.1157, longitude=13.3615, arpa_region="ARPA_SICILIA",
    ),
    "95100": ZipLocation(
        zip_code="95100", city="Catania", region="Sicilia",
        latitude=37.5079, longitude=15.0830, arpa_region="ARPA_SICILIA",
    ),
    # --- Veneto ---
    "30100": ZipLocation(
        zip_code="30100", city="Venezia", region="Veneto",
        latitude=45.4408, longitude=12.3155, arpa_region="ARPA_VENETO",
    ),
    "37100": ZipLocation(
        zip_code="37100", city="Verona", region="Veneto",
        latitude=45.4384, longitude=10.9916, arpa_region="ARPA_VENETO",
    ),
    "35100": ZipLocation(
        zip_code="35100", city="Padova", region="Veneto",
        latitude=45.4064, longitude=11.8768, arpa_region="ARPA_VENETO",
    ),
    # --- Piemonte ---
    "10100": ZipLocation(
        zip_code="10100", city="Torino", region="Piemonte",
        latitude=45.0703, longitude=7.6869, arpa_region="ARPA_PIEMONTE",
    ),
    # --- Emilia-Romagna ---
    "40100": ZipLocation(
        zip_code="40100", city="Bologna", region="Emilia-Romagna",
        latitude=44.4949, longitude=11.3426, arpa_region="ARPAE_EMILIA_ROMAGNA",
    ),
    "43100": ZipLocation(
        zip_code="43100", city="Parma", region="Emilia-Romagna",
        latitude=44.8015, longitude=10.3279, arpa_region="ARPAE_EMILIA_ROMAGNA",
    ),
    # --- Puglia ---
    "70100": ZipLocation(
        zip_code="70100", city="Bari", region="Puglia",
        latitude=41.1171, longitude=16.8719, arpa_region="ARPA_PUGLIA",
    ),
    # --- Toscana ---
    "50100": ZipLocation(
        zip_code="50100", city="Firenze", region="Toscana",
        latitude=43.7696, longitude=11.2558, arpa_region="ARPA_TOSCANA",
    ),
    "56100": ZipLocation(
        zip_code="56100", city="Pisa", region="Toscana",
        latitude=43.7228, longitude=10.4017, arpa_region="ARPA_TOSCANA",
    ),
    # --- Calabria ---
    "88100": ZipLocation(
        zip_code="88100", city="Catanzaro", region="Calabria",
        latitude=38.9054, longitude=16.5942, arpa_region="ARPA_CALABRIA",
    ),
    "89100": ZipLocation(
        zip_code="89100", city="Reggio Calabria", region="Calabria",
        latitude=38.1114, longitude=15.6473, arpa_region="ARPA_CALABRIA",
    ),
    # --- Sardegna ---
    "09100": ZipLocation(
        zip_code="09100", city="Cagliari", region="Sardegna",
        latitude=39.2238, longitude=9.1217, arpa_region="ARPA_SARDEGNA",
    ),
    # --- Liguria ---
    "16100": ZipLocation(
        zip_code="16100", city="Genova", region="Liguria",
        latitude=44.4056, longitude=8.9463, arpa_region="ARPA_LIGURIA",
    ),
    # --- Marche ---
    "60100": ZipLocation(
        zip_code="60100", city="Ancona", region="Marche",
        latitude=43.6158, longitude=13.5189, arpa_region="ARPA_MARCHE",
    ),
    # --- Abruzzo ---
    "67100": ZipLocation(
        zip_code="67100", city="L'Aquila", region="Abruzzo",
        latitude=42.3498, longitude=13.3995, arpa_region="ARTA_ABRUZZO",
    ),
    "65100": ZipLocation(
        zip_code="65100", city="Pescara", region="Abruzzo",
        latitude=42.4618, longitude=14.2161, arpa_region="ARTA_ABRUZZO",
    ),
    # --- Trentino-Alto Adige ---
    "38100": ZipLocation(
        zip_code="38100", city="Trento", region="Trentino-Alto Adige",
        latitude=46.0747, longitude=11.1217, arpa_region="APPA_TRENTO",
    ),
    "39100": ZipLocation(
        zip_code="39100", city="Bolzano", region="Trentino-Alto Adige",
        latitude=46.4983, longitude=11.3548, arpa_region="APPA_BOLZANO",
    ),
    # --- Friuli Venezia Giulia ---
    "34100": ZipLocation(
        zip_code="34100", city="Trieste", region="Friuli Venezia Giulia",
        latitude=45.6495, longitude=13.7768, arpa_region="ARPA_FVG",
    ),
    # --- Umbria ---
    "06100": ZipLocation(
        zip_code="06100", city="Perugia", region="Umbria",
        latitude=43.1107, longitude=12.3908, arpa_region="ARPA_UMBRIA",
    ),
    # --- Basilicata ---
    "85100": ZipLocation(
        zip_code="85100", city="Potenza", region="Basilicata",
        latitude=40.6404, longitude=15.8056, arpa_region="ARPA_BASILICATA",
    ),
    # --- Molise ---
    "86100": ZipLocation(
        zip_code="86100", city="Campobasso", region="Molise",
        latitude=41.5603, longitude=14.6684, arpa_region="ARPA_MOLISE",
    ),
    # --- Valle d'Aosta ---
    "11100": ZipLocation(
        zip_code="11100", city="Aosta", region="Valle d'Aosta",
        latitude=45.7370, longitude=7.3150, arpa_region="ARPA_VDA",
    ),
}


def get_zip_location(zip_code: str) -> ZipLocation | None:
    """Look up a ZIP code and return its location data, or None if unknown."""
    return ZIP_COORDINATE_MAP.get(zip_code)
