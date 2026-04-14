#!/bin/bash

echo "=== ML API Router DB ==="

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

if ! docker info > /dev/null 2>&1; then
    echo "BLAD: Docker nie jest uruchomiony."
    exit 1
fi

echo "Uruchamianie serwisów baz danych..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d redis_routes postgres_meta
else
    docker compose up -d redis_routes postgres_meta
fi

if [ $? -eq 0 ]; then
    echo "=== Sukces ==="
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
else
    echo "BŁĄD: docker-compose zwrócił błąd."
    exit 1
fi