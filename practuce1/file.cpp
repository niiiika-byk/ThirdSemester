#include <iostream>
#include <vector>
#include <string>
#include <ctime>
#include <cstdlib>
#include <algorithm>
#include <thread>
#include <chrono>

//база данных для хранения пассажиров
class Passenger {
private:
    std::string name;
    std::string flightNumber;
    bool isSuspicious;
    std::string status;
    time_t startTime;

public:
    Passenger(std::string name, std::string flight, bool suspicious)
        : name(std::move(name)), flightNumber(std::move(flight)), isSuspicious(suspicious), status("Регистрация"), startTime(time(0)) {}

    std::string get_name() const {
        return name;
    }

    std::string getFlightNumber() const {
        return flightNumber;
    }

    bool get_isSuspicious() const {
        return isSuspicious;
    }

    std::string get_status() const {
        return status;
    }

    time_t get_startTime() const {
        return startTime;
    }

    void set_status(const std::string& newStatus) {
        status = newStatus;
    }

    void set_startTime(time_t newStartTime) {
        startTime = newStartTime;
    }

    //завершена ли посадка
    bool is_completed() const {
        return status == "Удален из списка";
    }
};

//бизнес логика приложения
class Flight {
private:
    std::string flightNumber;
    std::vector<Passenger> passengers;

public:
    Flight(std::string flight) : flightNumber(std::move(flight)) {}

    std::string get_flightNumber() const {
        return flightNumber;
    }

    const std::vector<Passenger>& get_passengers() const {
        return passengers;
    }

    //добавление пассажира
    void add_passenger(const Passenger& passenger) {
        passengers.push_back(passenger);
    }

    //если посадка завершена, убираем с наблюдения
    void remove_completed() {
        passengers.erase(std::remove_if(passengers.begin(), passengers.end(), [](const Passenger& passenger) {
            return passenger.is_completed();
        }), passengers.end());
    }

    //нахождение пассажиров в аэропорте
    void update_status() {
        for (auto& passenger : passengers) {
            time_t currentTime = time(0);
            time_t elapsedTime = currentTime - passenger.get_startTime();

            if (passenger.get_status() == "Регистрация" && elapsedTime >= 60) {
                passenger.set_status("Досмотр");
                passenger.set_startTime(currentTime);
            } else if (passenger.get_status() == "Досмотр" && elapsedTime >= 60) {
                passenger.set_status("Таможня");
                passenger.set_startTime(currentTime);
            } else if (passenger.get_status() == "Таможня" && elapsedTime >= 60) {
                passenger.set_status("Зона ожидания");
                passenger.set_startTime(currentTime);
            } else if (passenger.get_status() == "Зона ожидания" && elapsedTime >= 300) {
                passenger.set_status("Зона посадки");
                passenger.set_startTime(currentTime);
            } else if (passenger.get_status() == "Зона посадки" && elapsedTime >= 60) {
                passenger.set_status("Пройдена посадка");
                passenger.set_startTime(currentTime);
            } else if (passenger.get_status() == "Пройдена посадка" && elapsedTime >= 180) {
                passenger.set_status("Удален из списка");
            }
        }
    }

    // Показать подозрительных пассажиров
    void display_suspicious() const {
        bool foundSuspicious = false;
        for (const auto& passenger : passengers) {
            if (passenger.get_isSuspicious()) {
                if (!foundSuspicious) {
                    std::cout << "Рейс " << flightNumber << ":" << std::endl;
                    foundSuspicious = true;
                }
                std::cout << " - " << passenger.get_name() << ": " << passenger.get_status() << std::endl;
            } else {
                std::cout << "Нет подозрительных пассажиров" << std::endl;
                std::cout << "--------------------------------------------------" << std::endl;
            }
        }
        if (foundSuspicious) {
            std::cout << "--------------------------------------------------" << std::endl;
        }
        
        std::cout << "\n";
    }
};

//база данных предыдущих инцидентов
bool is_suspicious() {
    //int randomValue = rand() % 100;
    //return randomValue < 5; //5% шанс быть подозрительным
    return rand() % 2; //50% шанс быть подозрительным
}

//API
void console_menu() {
    std::vector<Flight> flights;
    srand(static_cast<unsigned int>(time(0)));

    while (true) {
        std::cout << ">>> Выберите действие: " << std::endl;
        std::cout << "1. Зарегистрировать пассажира" << std::endl;
        std::cout << "2. Посмотреть подозрительных пассажиров и их статусы" << std::endl;
        
        std::cout << "--------------------------------------------------" << std::endl;

        int choice;
        std::cin >> choice;
        std::cin.ignore();

        switch (choice) {
        case 1: {
            std::string name, flightNumber;
            std::cout << ">>> Введите фамилию пассажира: ";
            std::getline(std::cin, name);
            std::cout << ">>> Введите номер рейса: ";
            std::getline(std::cin, flightNumber);

            //есть ли такой рейс
            auto it = std::find_if(flights.begin(), flights.end(), [&flightNumber](const Flight& flight) {
                return flight.get_flightNumber() == flightNumber;
            });

            bool suspicious = is_suspicious();
            Passenger newPassenger(name, flightNumber, suspicious);

            if (it != flights.end()) {
                it->add_passenger(newPassenger);
            } else {
                Flight newFlight(flightNumber);
                newFlight.add_passenger(newPassenger);
                flights.push_back(newFlight);
            }

            std::cout << "--------------------------------------------------" << std::endl;
            std::cout << "Пассажир " << name << " зарегистрирован на рейс " << flightNumber << "." << std::endl;
            std::cout << "Статус подозрительности: " << (suspicious ? "Подозрительный" : "Не подозрительный") << std::endl;
            std::cout << "--------------------------------------------------\n" << std::endl;
            break;
        }
        case 2: {
            if (flights.empty()) {
                std::cout << "Нет зарегистрированных рейсов.\n" << std::endl;
            } else {
                for (auto& flight : flights) {
                    flight.update_status(); //обновляем статусы
                    flight.remove_completed(); //удаляем улетевших                
                    flight.display_suspicious(); //показываем подозрительных
                }
            }
            break;
        }
        default:
            std::cout << "Неверный выбор. Попробуйте снова.\n" << std::endl;
            break;
        }

        std::this_thread::sleep_for(std::chrono::seconds(2));
    }
}

int main() {
    console_menu();
    return 0;
}