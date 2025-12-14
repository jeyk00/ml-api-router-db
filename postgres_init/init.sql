-- 1. TABELA REJESTRU 
CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) UNIQUE NOT NULL,
    health_status VARCHAR(20) DEFAULT 'OK',
    last_called_at TIMESTAMP,                
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELA METRYK (Zaktualizowana o koniec okna)
CREATE TABLE IF NOT EXISTS model_usage_metrics (
    model_name VARCHAR(100) NOT NULL,
    
    time_window_start TIMESTAMP NOT NULL,  -- Początek okna
    time_window_end TIMESTAMP NOT NULL,    -- Koniec okna
    
    request_count INTEGER DEFAULT 0,
    
    -- Klucz złożony: Start okna definiuje unikalność w danym okresie
    PRIMARY KEY (model_name, time_window_start),
    
    CONSTRAINT fk_model_registry 
        FOREIGN KEY(model_name) 
        REFERENCES model_registry(model_name)
        ON DELETE CASCADE
);

-- SEED DATA
INSERT INTO model_registry (model_name, health_status, last_called_at) 
VALUES ('digit-recognizer-v1', 'OK', NOW())
ON CONFLICT DO NOTHING;

