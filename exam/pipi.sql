/*1 билет*/
-- 2 вопрос

-- Создание таблицы Employees (Сотрудники)
CREATE TABLE Employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    email VARCHAR(100) UNIQUE
);

-- Создание таблицы Sources (Источники угроз)
CREATE TABLE Sources (
    source_id INT PRIMARY KEY AUTO_INCREMENT,
    source_type VARCHAR(50) NOT NULL,  -- IP, Domain, URL и т.д.
    source_value VARCHAR(255) NOT NULL, -- Например, "192.168.1.1"
    is_malicious BOOLEAN DEFAULT FALSE,
    first_detected DATE
);

-- Создание таблицы Vulnerabilities (Уязвимости)
CREATE TABLE Vulnerabilities (
    vulnerability_id INT PRIMARY KEY AUTO_INCREMENT,
    cve_id VARCHAR(20) UNIQUE NOT NULL,  -- Например, "CVE-2023-1234"
    description TEXT,
    severity VARCHAR(10) CHECK (severity IN ('Low', 'Medium', 'High', 'Critical'))
);

-- Создание таблицы Incidents (Инциденты)
CREATE TABLE Incidents (
    incident_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Closed')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    employee_id INT,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE SET NULL
);

-- Связующая таблица для связи M:N между Incidents и Vulnerabilities
CREATE TABLE IncidentVulnerabilities (
    incident_id INT,
    vulnerability_id INT,
    PRIMARY KEY (incident_id, vulnerability_id),
    FOREIGN KEY (incident_id) REFERENCES Incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (vulnerability_id) REFERENCES Vulnerabilities(vulnerability_id) ON DELETE CASCADE
);

-- Таблица для связи 1:M между Incidents и Sources (один инцидент → несколько источников)
CREATE TABLE IncidentSources (
    incident_id INT,
    source_id INT,
    PRIMARY KEY (incident_id, source_id),
    FOREIGN KEY (incident_id) REFERENCES Incidents(incident_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES Sources(source_id) ON DELETE CASCADE
);


-- 3 вопрос
WITH AvgThreatLevel AS (
    -- Вычисляем средний уровень угрозы по всем инцидентам
    SELECT AVG(threat_level) AS avg_threat
    FROM Incidents
)
SELECT 
    i.incident_type,
    COUNT(*) AS incident_count,
    GROUP_CONCAT(DISTINCT e.full_name ORDER BY e.full_name SEPARATOR ', ') AS assigned_employees
FROM 
    Incidents i
JOIN 
    Employees e ON i.employee_id = e.employee_id
CROSS JOIN 
    AvgThreatLevel atl
WHERE 
    i.status <> 'Closed'
    AND i.threat_level > atl.avg_threat  -- Фильтр по уровню угрозы выше среднего
GROUP BY 
    i.incident_type
ORDER BY 
    incident_count DESC;

/*2 билет*/
-- 3 вопрос

CREATE FUNCTION fn_avg_response_time(employee_id INT) 
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE avg_time DECIMAL(10,2);
    SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) INTO avg_time
    FROM Incidents
    WHERE employee_id = employee_id AND resolved_at IS NOT NULL;
    RETURN IFNULL(avg_time, 0);
END;

-- Пример вызова:
SELECT employee_id, full_name, fn_avg_response_time(employee_id) AS avg_hours
FROM Employees
WHERE employee_id = 5;

-- Для PostgreSQL (с проверкой диапазона)
CREATE OR REPLACE FUNCTION fn_threat_validation(incident_id INT) 
RETURNS BOOLEAN AS $$
DECLARE
    threat_level INT;
BEGIN
    SELECT i.threat_level INTO threat_level
    FROM Incidents i
    WHERE i.incident_id = $1;
    
    RETURN (threat_level BETWEEN 1 AND 5);
END;
$$ LANGUAGE plpgsql;

-- Пример вызова:
SELECT incident_id, title, threat_level, fn_threat_validation(incident_id) AS is_valid
FROM Incidents
WHERE incident_id = 100;

--4 билет
--3 вопрос

-- Создаем таблицу для логов (если еще не создана)
CREATE TABLE IF NOT EXISTS Incidents_Log (
    log_id SERIAL PRIMARY KEY,
    operation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operation_user VARCHAR(100) NOT NULL,
    incident_id INT NOT NULL,
    incident_data JSONB NOT NULL,
    operation_type VARCHAR(10) NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE'))
);

-- Триггер для проверки threat_level перед вставкой
CREATE OR REPLACE TRIGGER validate_incident_threat
BEFORE INSERT ON Incidents
FOR EACH ROW
EXECUTE FUNCTION 
BEGIN
    -- Проверяем и корректируем threat_level
    IF NEW.threat_level IS NULL OR NEW.threat_level < 1 OR NEW.threat_level > 5 THEN
        NEW.threat_level := 3; -- Устанавливаем значение по умолчанию
    END IF;
    
    RETURN NEW;
END;

-- Триггер для логирования после вставки
CREATE OR REPLACE TRIGGER log_incident_insert
AFTER INSERT ON Incidents
FOR EACH ROW
EXECUTE FUNCTION 
BEGIN
    -- Логируем операцию вставки
    INSERT INTO Incidents_Log (
        operation_date,
        operation_user,
        incident_id,
        incident_data,
        operation_type
    ) VALUES (
        CURRENT_TIMESTAMP,
        CURRENT_USER,
        NEW.incident_id,
        jsonb_build_object(
            'title', NEW.title,
            'description', NEW.description,
            'status', NEW.status,
            'threat_level', NEW.threat_level,
            'created_at', NEW.created_at,
            'updated_at', NEW.updated_at
        ),
        'INSERT'
    );
    
    RETURN NULL;
END;

--5 билет
--3 вопрос

SELECT 
    incident_type,
    COUNT(*) AS incident_count,
    AVG(threat_level) AS avg_threat_level,
    MAX(created_at) AS last_incident_date
FROM (
    -- Подзапрос как временная таблица
    SELECT 
        id,
        incident_type,
        threat_level,
        created_at
    FROM incidents
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
) AS recent_incidents
GROUP BY incident_type
HAVING AVG(threat_level) > 3
ORDER BY avg_threat_level DESC;