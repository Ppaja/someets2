#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Skript für die Pfalz-Mod Karte
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def show_mod_map_overview():
    """Zeigt Übersicht der Mod-Karte"""
    print("🗺️  PFALZ-MOD KARTE ÜBERSICHT")
    print("=" * 60)
    
    try:
        from src.config import PROFILE_PATH
        from src.game_integration.ets2_savegame_parser import SavegameParser
        
        parser = SavegameParser(profile_path=PROFILE_PATH)
        cities = parser.get_available_cities()
        
        print(f"🏙️  {len(cities)} Städte in der Mod:")
        for i, city in enumerate(sorted(cities), 1):
            print(f"{i:2d}. {city}")
        
        return cities
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return []

def analyze_job_distribution():
    """Analysiert Auftragsverteilung pro Stadt"""
    print(f"\n📊 AUFTRAGSVERTEILUNG PRO STADT")
    print("=" * 60)
    
    try:
        from src.config import PROFILE_PATH
        from src.game_integration.ets2_savegame_parser import SavegameParser
        
        parser = SavegameParser(profile_path=PROFILE_PATH)
        cities = parser.get_available_cities()
        
        job_stats = []
        
        for city in cities:
            try:
                jobs = parser.get_freight_market_jobs(start_city=city)
                job_count = len(jobs) if jobs else 0
                
                # Berechne durchschnittliche Distanz
                avg_distance = 0
                if jobs:
                    avg_distance = sum(job['distance_km'] for job in jobs) / len(jobs)
                
                job_stats.append({
                    'city': city,
                    'job_count': job_count,
                    'avg_distance': avg_distance
                })
                
            except Exception as e:
                job_stats.append({
                    'city': city,
                    'job_count': 0,
                    'avg_distance': 0,
                    'error': str(e)
                })
        
        # Sortiere nach Anzahl Jobs
        job_stats.sort(key=lambda x: x['job_count'], reverse=True)
        
        print("📋 JOBS PRO STADT (sortiert nach Anzahl):")
        print("-" * 50)
        print(f"{'Stadt':<12} {'Jobs':<6} {'Ø Distanz':<10} {'Status'}")
        print("-" * 50)
        
        for stat in job_stats:
            status = "❌ Fehler" if 'error' in stat else "✅"
            avg_dist = f"{stat['avg_distance']:.1f} km" if stat['avg_distance'] > 0 else "-"
            
            print(f"{stat['city']:<12} {stat['job_count']:<6} {avg_dist:<10} {status}")
        
        # Statistiken
        total_jobs = sum(s['job_count'] for s in job_stats)
        active_cities = len([s for s in job_stats if s['job_count'] > 0])
        
        print(f"\n📈 STATISTIKEN:")
        print(f"   Gesamt Jobs: {total_jobs}")
        print(f"   Aktive Städte: {active_cities}/{len(cities)}")
        print(f"   Ø Jobs pro Stadt: {total_jobs/len(cities):.1f}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

def show_cargo_types():
    """Zeigt alle verfügbaren Frachttypen"""
    print(f"\n📦 FRACHTTYPEN IN DER MOD")
    print("=" * 60)
    
    try:
        from src.utils.translation import CARGO_MAP
        
        print(f"📋 {len(CARGO_MAP)} Frachttypen verfügbar:")
        print("-" * 40)
        print(f"{'Intern':<15} {'Anzeige'}")
        print("-" * 40)
        
        for internal, display in sorted(CARGO_MAP.items()):
            print(f"{internal:<15} {display}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

def show_companies():
    """Zeigt alle verfügbaren Firmen"""
    print(f"\n🏢 FIRMEN IN DER MOD")
    print("=" * 60)
    
    try:
        from src.utils.translation import COMPANY_MAP
        
        print(f"📋 {len(COMPANY_MAP)} Firmen verfügbar:")
        print("-" * 40)
        print(f"{'Intern':<15} {'Anzeige'}")
        print("-" * 40)
        
        for internal, display in sorted(COMPANY_MAP.items()):
            print(f"{internal:<15} {display}")
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

def test_realistic_job_request():
    """Testet realistische Auftragsanforderung"""
    print(f"\n🚛 REALISTISCHE AUFTRAGSANFORDERUNG")
    print("=" * 60)
    
    try:
        from src.actions.job_actions import process_job_request_async
        from src.config import PROFILE_PATH
        from src.game_integration.ets2_savegame_parser import SavegameParser
        
        parser = SavegameParser(profile_path=PROFILE_PATH)
        cities = parser.get_available_cities()
        
        # Teste mit Stadt mit den meisten Jobs
        jobs_per_city = {}
        for city in cities:
            try:
                jobs = parser.get_freight_market_jobs(start_city=city)
                jobs_per_city[city] = len(jobs) if jobs else 0
            except:
                jobs_per_city[city] = 0
        
        best_city = max(jobs_per_city, key=jobs_per_city.get)
        
        print(f"🎯 Teste mit Stadt: {best_city} ({jobs_per_city[best_city]} Jobs)")
        
        # Zeige was passieren würde
        print(f"\n📱 Simulierter Ablauf:")
        print(f"1. Spieler: 'Bin in {best_city}, brauche neuen Auftrag.'")
        print(f"2. System: process_job_request_async('{best_city}')")
        print(f"3. Parser: get_freight_market_jobs(start_city='{best_city}')")
        print(f"4. Gefunden: {jobs_per_city[best_city]} verfügbare Jobs")
        print(f"5. KI wählt besten Job aus")
        print(f"6. Dispo antwortet mit Auftragsdetails")
        
        # Zeige verfügbare Jobs
        jobs = parser.get_freight_market_jobs(start_city=best_city)
        if jobs:
            print(f"\n📋 Verfügbare Jobs von {best_city}:")
            print("-" * 50)
            
            for i, job in enumerate(jobs[:5], 1):  # Erste 5
                print(f"{i}. {job['start_company']} → {job['target_company']}")
                print(f"   {job['cargo']}, {job['distance_km']} km nach {job['target_city']}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    cities = show_mod_map_overview()
    
    if cities:
        analyze_job_distribution()
        show_cargo_types()
        show_companies()
        test_realistic_job_request()
    
    print("\n" + "=" * 60)
    print("PFALZ-MOD ANALYSE ABGESCHLOSSEN")
    print("=" * 60)
