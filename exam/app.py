from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SeverityLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

@dataclass
class Vulnerability:
    id: int
    title: str
    description: str
    discovery_date: datetime
    fix_date: datetime = None
    status: str = "Open"
    severity: SeverityLevel = SeverityLevel.MEDIUM

class VulnerabilityRepository:
    def __init__(self):
        self._vulnerabilities = []
        self._next_id = 1

    def add(self, vulnerability: Vulnerability) -> Vulnerability:
        vulnerability.id = self._next_id
        self._next_id += 1
        self._vulnerabilities.append(vulnerability)
        return vulnerability

    def get_all(self) -> list[Vulnerability]:
        return self._vulnerabilities.copy()

    def get_by_id(self, id: int) -> Vulnerability | None:
        for vuln in self._vulnerabilities:
            if vuln.id == id:
                return vuln
        return None

    def update(self, vulnerability: Vulnerability) -> bool:
        for i, vuln in enumerate(self._vulnerabilities):
            if vuln.id == vulnerability.id:
                self._vulnerabilities[i] = vulnerability
                return True
        return False

class VulnerabilityService:
    def __init__(self, repository):
        self.repository = repository

    def add_vulnerability(self, title: str, description: str, severity: SeverityLevel) -> Vulnerability:
        if not title:
            raise ValueError("Title is required")
        
        if len(title) > 100:
            raise ValueError("Title is too long (max 100 chars)")
        
        vuln = Vulnerability(
            id=0,  # Will be set by repository
            title=title,
            description=description,
            discovery_date=datetime.now(),
            severity=severity
        )
        return self.repository.add(vuln)

    def close_vulnerability(self, id: int, fix_date: datetime) -> bool:
        vuln = self.repository.get_by_id(id)
        if not vuln:
            raise ValueError("Vulnerability not found")
        
        if fix_date < vuln.discovery_date:
            raise ValueError("Fix date cannot be before discovery date")
        
        vuln.status = "Closed"
        vuln.fix_date = fix_date
        return self.repository.update(vuln)

    def get_all_vulnerabilities(self) -> list[Vulnerability]:
        return self.repository.get_all()

def print_menu():
    print("\nVulnerability Management System")
    print("1. Add Vulnerability")
    print("2. Show All Vulnerabilities")
    print("3. Close Vulnerability")
    print("4. Exit")

def print_vulnerabilities(vulnerabilities):
    print("\nID\tTitle\t\tStatus\tSeverity\tDiscovery Date")
    for vuln in vulnerabilities:
        print(f"{vuln.id}\t{vuln.title[:10]}...\t{vuln.status}\t{vuln.severity.value}\t{vuln.discovery_date.strftime('%Y-%m-%d')}")

def main():
    repository = VulnerabilityRepository()
    service = VulnerabilityService(repository)

    while True:
        print_menu()
        choice = input("Select option: ")

        try:
            if choice == "1":
                title = input("Title: ")
                description = input("Description: ")
                print("Severity levels:")
                for i, level in enumerate(SeverityLevel, 1):
                    print(f"{i}. {level.value}")
                severity_choice = int(input("Select severity (1-4): ")) - 1
                severity = list(SeverityLevel)[severity_choice]
                
                vuln = service.add_vulnerability(title, description, severity)
                print(f"Vulnerability added with ID: {vuln.id}")

            elif choice == "2":
                vulns = service.get_all_vulnerabilities()
                print_vulnerabilities(vulns)

            elif choice == "3":
                vuln_id = int(input("Enter vulnerability ID to close: "))
                fix_date_str = input("Fix date (YYYY-MM-DD): ")
                fix_date = datetime.strptime(fix_date_str, "%Y-%m-%d")
                
                if service.close_vulnerability(vuln_id, fix_date):
                    print("Vulnerability closed successfully")
                else:
                    print("Failed to close vulnerability")

            elif choice == "4":
                print("Exiting...")
                break

            else:
                print("Invalid option")

        except ValueError as e:
            print(f"Error: {e}")
        except IndexError:
            print("Error: Invalid severity level")
        except Exception as e:
            print(f"Unexpected error: {e}")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()