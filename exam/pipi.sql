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

--6 билет
--3 вопрос

CREATE OR REPLACE FUNCTION count_vulnerabilities_in_period(
    start_date DATE,
    end_date DATE
)
RETURNS INTEGER AS $$
DECLARE
    vulnerability_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO vulnerability_count
    FROM vulnerabilities
    WHERE created_at BETWEEN start_date AND end_date;
    
    -- Возвращаем 0 если нет результатов
    RETURN COALESCE(vulnerability_count, 0);
END;
$$ LANGUAGE plpgsql;

--проверка
SELECT 
    count_vulnerabilities_in_period(
        '2023-01-01', 
        '2023-12-31'
    ) AS vulnerabilities_count;

--7 билет
--2 вопрос
CREATE TABLE IF NOT EXISTS vulnerability_audit (
    audit_id SERIAL PRIMARY KEY,
    vulnerability_id INT NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    audit_message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities(vulnerability_id)
);

CREATE OR REPLACE FUNCTION check_incidents_after_vulnerability_fix()
RETURNS TRIGGER AS $$
DECLARE
    open_incidents_count INTEGER;
BEGIN
    -- Проверяем, изменился ли статус на "Fixed"
    IF NEW.status = 'Fixed' AND OLD.status != 'Fixed' THEN
        -- Проверяем наличие связанных открытых инцидентов
        SELECT COUNT(*) INTO open_incidents_count
        FROM incident_vulnerabilities iv
        JOIN incidents i ON iv.incident_id = i.incident_id
        WHERE iv.vulnerability_id = NEW.vulnerability_id
        AND i.status = 'Open';
        
        -- Если есть открытые инциденты
        IF open_incidents_count > 0 THEN
            -- Вариант 1: Обновляем статус инцидентов
            UPDATE incidents
            SET status = 'Needs re-check',
                updated_at = CURRENT_TIMESTAMP
            WHERE incident_id IN (
                SELECT incident_id 
                FROM incident_vulnerabilities
                WHERE vulnerability_id = NEW.vulnerability_id
            ) AND status = 'Open';
            
            -- Вариант 2: Добавляем запись в аудит
            INSERT INTO vulnerability_audit (
                vulnerability_id,
                old_status,
                new_status,
                audit_message
            ) VALUES (
                NEW.vulnerability_id,
                OLD.status,
                NEW.status,
                'Vulnerability marked as fixed, but ' || open_incidents_count || 
                ' open incidents depend on it. Status changed to "Needs re-check".'
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_vulnerability_status_update
AFTER UPDATE ON vulnerabilities
FOR EACH ROW
EXECUTE FUNCTION check_incidents_after_vulnerability_fix();

--3 вопрос
CREATE OR REPLACE VIEW OpenIncidentsByEmployee AS
SELECT 
    i.assigned_employee_id AS employee_id,
    COUNT(i.incident_id) AS count_of_open_incidents,
    ROUND(AVG(i.threat_level), 2) AS avg_threat_level
FROM 
    Incidents i
WHERE 
    i.status = 'Open'
GROUP BY 
    i.assigned_employee_id;

--использование
-- Получить статистику по всем сотрудникам
SELECT * FROM OpenIncidentsByEmployee
ORDER BY count_of_open_incidents DESC;

-- Получить данные для конкретного сотрудника
SELECT * FROM OpenIncidentsByEmployee
WHERE employee_id = 123;

--8 билет
--3 вопрос
SELECT 
    i.incident_id,
    i.title AS incident_title,
    i.status,
    i.created_at AS incident_date,
    s.source_id,
    s.source_type,
    s.source_value,
    s.is_malicious
FROM 
    incidents i
INNER JOIN 
    incident_sources is ON i.incident_id = is.incident_id
INNER JOIN 
    sources s ON is.source_id = s.source_id
ORDER BY 
    i.created_at DESC;

SELECT 
    s.source_id,
    s.source_type,
    s.source_value,
    s.is_malicious,
    s.first_detected,
    i.incident_id,
    i.title AS incident_title,
    i.status
FROM 
    sources s
LEFT JOIN 
    incident_sources is ON s.source_id = is.source_id
LEFT JOIN 
    incidents i ON is.incident_id = i.incident_id
ORDER BY 
    s.source_id;

--9 билет 
--2 задание
CREATE TABLE Incident_Employee (
    incident_id INT NOT NULL,
    employee_id INT NOT NULL,
    role_on_incident VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (incident_id, employee_id),
    FOREIGN KEY (incident_id) REFERENCES Incidents(id),
    FOREIGN KEY (employee_id) REFERENCES Employees(id),
    
    INDEX (incident_id),
    INDEX (employee_id)

--3 задание
-- Таблица сотрудников
CREATE TABLE Employees (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Таблица инцидентов
CREATE TABLE Incidents (
    id INT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('OPEN', 'CLOSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица-связка
CREATE TABLE Incident_Employee (
    incident_id INT NOT NULL,
    employee_id INT NOT NULL,
    role_on_incident VARCHAR(100) NOT NULL,
    PRIMARY KEY (incident_id, employee_id),
    FOREIGN KEY (incident_id) REFERENCES Incidents(id),
    FOREIGN KEY (employee_id) REFERENCES Employees(id)
);

CREATE TRIGGER prevent_employee_deletion
BEFORE DELETE ON Employees
FOR EACH ROW
BEGIN
    DECLARE open_incidents_count INT;
    
    -- Проверяем количество открытых инцидентов у сотрудника
    SELECT COUNT(*) INTO open_incidents_count
    FROM Incident_Employee ie
    JOIN Incidents i ON ie.incident_id = i.id
    WHERE ie.employee_id = OLD.id AND i.status = 'OPEN';
    
    -- Если есть открытые инциденты, запрещаем удаление
    IF open_incidents_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Нельзя удалить сотрудника, привязанного к открытым инцидентам';
    END IF;
END

-- 1. Добавляем тестовые данные
INSERT INTO Employees (id, name) VALUES 
(1, 'Иван Петров'),
(2, 'Мария Сидорова'),
(3, 'Алексей Иванов');

INSERT INTO Incidents (id, title, status) VALUES 
(101, 'Сбой в системе', 'OPEN'),
(102, 'Обновление ПО', 'CLOSED'),
(103, 'Проблема с сетью', 'OPEN');

INSERT INTO Incident_Employee (incident_id, employee_id, role_on_incident) VALUES 
(101, 1, 'Аналитик'),
(101, 2, 'Разработчик'),
(102, 1, 'Тестировщик'),
(103, 3, 'Руководитель');

-- 2. Пробуем удалить сотрудника без открытых инцидентов (должно разрешиться)
DELETE FROM Employees WHERE id = 1; -- Успешно, так как инцидент 102 закрыт

-- 3. Пробуем удалить сотрудника с открытыми инцидентами (должно запретиться)
DELETE FROM Employees WHERE id = 2; -- Ошибка: "Нельзя удалить сотрудника, привязанного к открытым инцидентам"

-- 4. Пробуем удалить другого сотрудника с открытыми инцидентами
DELETE FROM Employees WHERE id = 3; -- Ошибка: "Нельзя удалить сотрудника, привязанного к открытым инцидентам"

-- 5. Закрываем инцидент и пробуем снова
UPDATE Incidents SET status = 'CLOSED' WHERE id = 103;
DELETE FROM Employees WHERE id = 3; -- Теперь удаление пройдет успешно