-- 1. TABELA REJESTRU 
-- Przechowuje aktualny stan i metadane modelu.
CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) UNIQUE NOT NULL, -- np. 'digit-recognizer-v1'
    health_status VARCHAR(20) DEFAULT 'OK',  -- Status: 'OK', 'ERROR', 'LOADING'
    last_called_at TIMESTAMP,                
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

-- 2. TABELA METRYK
-- Przechowuje historię obciążenia w oknach czasowych.
CREATE TABLE IF NOT EXISTS model_usage_metrics (
    model_name VARCHAR(100) NOT NULL,
    time_window TIMESTAMP NOT NULL,       -- Początek okna, np. 14:00, 14:15
    request_count INTEGER DEFAULT 0,      -- Licznik requestów w tym oknie
    
    -- Klucz złożony: Jeden wpis na model w danym oknie czasowym
    PRIMARY KEY (model_name, time_window),
    
    CONSTRAINT fk_model_registry --Przed wprowadzeniem danych dla modelu wymagane jest zarejestrownaie go
        FOREIGN KEY(model_name) 
        REFERENCES model_registry(model_name)
        ON DELETE CASCADE
);

INSERT INTO model_registry (model_name, health_status, last_called_at) 
VALUES ('digit-recognizer-v1', 'OK', NOW())
ON CONFLICT DO NOTHING;


