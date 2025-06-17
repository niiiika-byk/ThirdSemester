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

