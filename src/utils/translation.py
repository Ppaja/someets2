
# src/utils/translation.py
CITY_NAME_MAPPING = {
    "annweiler": "Annweiler",
    "bann": "Bann",
    "hauenstein": "Hauenstein",
    "hermhof": "Hermersbergerhof",
    "hhnoed": "Höheinöd",
    "hinterw": "Hinterweidenthal",
    "johannis": "Johanniskreuz",
    "leimen": "Leimen",
    "merzalben": "Merzalben",
    "munchweil": "Münchweiler",
    "pirmasens": "Pirmasens",
    "ps_nord": "Pirmasens",  
    "thr_fhn": "Thaleischweiler-Fröschen",
    "trippstadt": "Trippstadt",
    "waldburg": "Waldfischbach-Burgalben",
    "weselberg": "Weselberg",
}

COMPANY_MAP = {
    'abriss': '@@Abriss@@', 'aldi_sued': 'Aldi Süd Gmbh', 'b10_bau': 'Baustelle B10 Hinterweidenthal',
    'baulog_s': 'Steinbruch', 'baulog_w': 'Sanbuilders', 'buchm_log': 'Buchmann Gmbh - Tor 73',
    'buchmann': 'Buchmann Gmbh', 'bunker_b10': 'Bunker B10 Hinterweidenthal', 'bunker_maz': 'Bunker Merzalben',
    'bus_bahnhof': 'Bahnhof', 'bus_touri': 'Ausflugsziel', 'car_berndl': 'Auto Berndl',
    'car_euler': 'Euler Pirmasens Gmbh', 'chripa': 'Chripa Paletten Gmbh & Co. Kg', 'debnar_t': 'Debnar',
    'drinkskrebs': 'Getränke Krebs Gmbh', 'en_holz_fl': '@@Rpm En Holz Fl@@', 'etha_tec': '@@Etha Tec@@',
    'farm_depot': 'Farm Depot', 'farm_hof': 'Hof', 'feld_gras': '@@Feld Gras@@', 'feld_mais': '@@Feld Mais@@',
    'feld_stroh': '@@Feld Stroh@@', 'feld_stroh_2': '@@Feld Stroh 2@@', 'feld_sug': '@@Zuckerrübenfeld@@',
    'fuchshof': 'Fuchshof', 'heizoel_gwe': 'Gewerbe', 'heizoel_prt': 'Privathaus', 'hoka_con': '@@Hoka Con@@',
    'hoka_stl': 'Hoka Stahlbau Gmbh', 'hombrunner': 'Hombrunner', 'hornbach': 'Hornbach Gmbh',
    'huegel': 'Gebr. Hügel Transporte Gmbh', 'kaufland': 'Kaufland', 'kcfg': 'Kömmerling Gmbh',
    'kopp_verp': 'Kopp Verpackungen Gmbh', 'kuffenberg': 'Kuffenberg', 'lahner': 'Lahner Forst',
    'landesf_hq': 'Depot Landesforsten Rlp', 'landesforst': '@@Rpm Ln Forst Rp@@', 'lidl': 'Lidl Gmbh',
    'lithon_plus': '@@Rpm Ltn Ps@@', 'netto': 'Netto', 'nsy_gallucci': '@@Rpm Nsy Gali@@', 'pfalzgut': 'Pfalzgut',
    'progroup_bau': 'Progroup Baustelle', 'reisinger_abb': '@@Rabb@@', 'remondis': 'Remondis',
    'rpm_bau': '@@Rpm Bau@@', 'rpm_schutt': '@@Rpm Schutt@@', 'schmitt_uhg': 'Schmitt Unternehmensgruppe',
    'schuster_t': 'Schuster & Sohn Kg', 'shell_t': 'Shell Hinterweidenthal', 'solar': 'Solarpark',
    'sp': 'Schumacher Packaging Gmbh', 'spedi_hardt': '@@Rpm Spedi Hardt@@', 'staendenhof': 'Totalenergies Ständenhof',
    'staendenhof_t': 'Totalenergies Ständenhof Tankplatz', 'union_bau': '@@Rpm U Bau@@',
    'wagner_pv': 'Wagner Photovoltaik Company Gmbh', 'waldb_bau': 'Baustelle Waldburgalben',
    'wasgau': 'Wasgau Logistik', 'wawi': 'Wawi Schokolade ', 'wawi_t': 'Wawi Group',
    'werth_lager': 'Wertholzlager Landesforsten Rlp', 'wind_const': 'Baustelle Windkraftanlage',
    'wood_log': '@@Wood Log@@', 'wood_log_2': '@@Wood Log@@', 'nsy_gali': 'Nsy Gali', 'rabb': 'Rabb', 'tes_hof': 'Tes Hof',
}
CARGO_MAP = {
    'bales_gras': 'Grasballen', 'bales_straw': 'Strohballen', 'biodiesel': 'Biodiesel',
    'con_rubble': 'Bauschutt', 'drinks': 'Getränke', 'empties': 'Leergut', 'freme': 'Rahmenkonstruktion',
    'frozen_food': 'Tiefkühlkost', 'goat': 'Lebende Ziegen', 'heizoel_prt': 'Heizöl (raffiniert)',
    'heizoel_raf': 'Heizöl (Raffinerie)', 'holzaufsrah': 'Holz-Aufsatzrahmen', 'horses': 'Lebende Pferde',
    'kaffeefahrt': 'Kaffeefahrt', 'kaffeefahrt_out': 'Kaffeefahrt (Rückfahrt)', 'kcfg_frame': 'Konstruktionsrahmen',
    'log_empty': 'Leerer Holzrahmen', 'mehrw_cont': 'Mehrweg-Container', 'mopro': 'Molkereiprodukte',
    'new_palet': 'Leere Paletten', 'obge': 'Obst und Gemüse', 'obge_products': 'Obst- und Gemüseprodukte',
    'old_cable': 'Altkabel', 'papp_umver': 'Papp-Umverpackungen', 'passengers_01': 'Passagiere',
    'pigs': 'Lebende Schweine', 'pon_ergoh8': 'Industrieteile (Ergoh8)', 'sand': 'Sand',
    'schichtarbeiter': 'Schichtarbeiter', 'schichtarbeiter_out': 'Schichtarbeiter (Rückfahrt)',
    'schulausflug': 'Schulausflug', 'schulausflug_out': 'Schulausflug (Rückfahrt)', 'sev': 'Schienenersatzverkehr',
    'solarmod_b': 'Solarmodule', 'solarmod_c': 'Solarmodule', 'straw_bales': 'Strohballen',
    'touristen': 'Tagesausflug (Touristen)', 'touristen_out': 'Touristen (Rückfahrt)',
    'union_frame': 'Tragwerk (Union Frame)', 'used_cars': 'Gebrauchtwagen', 'waste': 'Restmüll',
    'wellpkart': 'Wellpappe', 'corn_b': 'Mais', 'holzh': 'Holzhackschnitzel', 'logs': 'Baumstämme',
    'sugar_beet_b': 'Zuckerrüben', 'wheat': 'Weizen', 'wood_bark': 'Baumrinde', 'wshavings': 'Holzspäne',
    'concr_beams2': 'Betonträger',
    'concr_cent': 'Beton',
    'concr_stair': 'Betontreppe',
    'electronics': 'Elektronikwaren',
    'empty_barr': 'Leere Fässer',
    'empty_palet': 'Leere Paletten',
    'emptytank': 'Leertank',
    'excav_soil': 'Aushuberde',
    'fuel_tanks': 'Kraftstofftanks',
    'gravel': 'Kies',
    'honey': 'Honig',
    'lumber': 'Schnittholz',
    'metal_pipes': 'Metallrohre',
    'milk_t': 'Milch (Tanker)',
    'motor_oil': 'Motoröl',
    'pot_flowers': 'Blumen in Töpfen',
    're_bars': 'Bewehrungsstahl',
    'rooflights': 'Dachleuchten',
    'sawpanels': 'Sägebretter',
    'scrap_metals': 'Altmetall',
    'stone_dust': 'Steinstaub',
    'stones': 'Steine',
    'tractors': 'Traktoren',
    'used_packag': 'Gebrauchte Verpackungen',
    'used_plast': 'Gebrauchter Kunststoff',
    'used_plast_c': 'Verdichteter Kunststoff',
    'watertank': 'Wassertank', 'cows': 'Lebende Kühe',
}
def get_pretty_city_name(raw_city_name: str) -> str:
    """Übersetzt einen rohen Stadtnamen in einen schönen Namen über das zentrale Mapping."""
    return CITY_NAME_MAPPING.get(raw_city_name.lower(), raw_city_name.capitalize())

def get_raw_city_names(pretty_city_name: str) -> list[str]:
    """Findet alle rohen Städtenamen, die zu einem schönen Namen gehören."""
    pretty_city_name = pretty_city_name.lower()
    return [raw for raw, pretty in CITY_NAME_MAPPING.items() if pretty.lower() == pretty_city_name]

def translate_name(dev_name, name_map):
    """Übersetzt einen Entwicklernamen in einen lesbaren Namen und bereinigt ihn."""
    if not isinstance(dev_name, str):
        return "N/A"
    clean_dev_name = dev_name.split('.')[-1]
    human_name = name_map.get(clean_dev_name.lower(), clean_dev_name.capitalize())
    if human_name.startswith('@@') and human_name.endswith('@@'):
        human_name = human_name.replace('@@', '').replace('_', ' ').title()
    return human_name

def get_human_job_details(job_data: dict) -> dict:
    """Übersetzt die Entwicklernamen in lesbare Namen für einen Job."""
    human_job = job_data.copy()
    human_job['source_company_human'] = translate_name(job_data.get('source_company_dev', 'N/A'), COMPANY_MAP)
    human_job['source_city_human'] = job_data.get('source_city_dev', 'N/A').capitalize()
    human_job['target_company_human'] = translate_name(job_data.get('target_company_dev', 'N/A'), COMPANY_MAP)
    human_job['target_city_human'] = job_data.get('target_city_dev', 'N/A').capitalize()
    human_job['cargo_human'] = translate_name(job_data.get('cargo_dev', 'N/A'), CARGO_MAP)
    return human_job