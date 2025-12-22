#!/bin/bash

echo "=== ML API Router DB ==="

# 1. Sprawdzenie pliku .env
if [ ! -f .env ]; then
    echo "Brak pliku .env."
    if [ -f .env.example ]; then
        echo "Tworzę plik .env na podstawie .env.example..."
        cp .env.example .env
    else
        echo "BLAD: Brak pliku .env.example. Nie można skonfigurować zmiennych środowiskowych."
        exit 1
    fi
fi

# 2. Sprawdzenie czy Docker działa
if ! docker info > /dev/null 2>&1; then
    echo "BLAD: Docker nie jest uruchomiony."
    exit 1
fi

# 3. Uruchomienie kontenerów
echo "Uruchamianie serwisów baz danych..."
# Używamy 'docker-compose' (V1) lub 'docker compose' (V2) w zależności od wersji
if command -v docker-compose &> /dev/null; then
    docker-compose up -d redis_routes postgres_meta
else
    docker compose up -d redis_routes postgres_meta
fi

# 4. Weryfikacja statusu
if [ $? -eq 0 ]; then
    echo "=== Sukces ==="
    # Podobnie tutaj - sprawdzenie wersji dla komendy ps
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
else
    echo "BŁĄD: docker-compose zwrócił błąd."
    exit 1
fi