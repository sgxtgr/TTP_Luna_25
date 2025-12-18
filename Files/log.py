import krpc
import time
import csv

def log_flight_data():
    print("Подключение к KSP...")
    try:
        conn = krpc.connect(name='Flight Logger')
    except ConnectionRefusedError:
        print("Ошибка!")
        return

    vessel = conn.space_center.active_vessel

    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    speed = conn.add_stream(getattr, vessel.flight(vessel.orbit.body.reference_frame), 'speed')
    mass = conn.add_stream(getattr, vessel, 'mass')
    
    filename = 'flight_data_soyuz.csv'
    
    print(f"Начинаю запись данных в {filename}...")
    print("Нажмите Ctrl+C для остановки записи.")

    start_time = ut()
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['time', 'altitude', 'speed', 'mass']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        try:
            while True:
                t = ut() - start_time
                alt = altitude()
                spd = speed()
                m = mass() * 1000
                writer.writerow({
                    'time': round(t, 2),
                    'altitude': round(alt, 2),
                    'speed': round(spd, 2),
                    'mass': round(m, 3) 
                })
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Запись остановлена пользователем.")
        except Exception as e:
            print(f"Ошибка при записи: {e}")
        finally:
            print(f"Данные сохранены в {filename}")

if __name__ == "__main__":
    log_flight_data()
