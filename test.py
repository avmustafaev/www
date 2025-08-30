# test.py
from modules.vmware_connector import VMwareConnector

def main():
    connector = VMwareConnector()
    
    try:
        # Подключение к VMware
        connector.connect()
        
        # Запрос имени виртуальной машины
        vm_name = input("Введите имя виртуальной машины: ").strip()
        if not vm_name:
            print("❌ Имя виртуальной машины не указано!")
            return
            
        # Выполнение команды в гостевой ОС
        command = "uptime && df -h"  # Можно изменить на нужную команду
        print(f"\nВыполняется команда: {command}")
        
        try:
            stdout = connector.execute_guest_command(vm_name, command)
            print("\nРезультат:")
            print(stdout)
        except Exception as e:
            print(f"❌ Ошибка выполнения команды: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Отключение
        connector.disconnect()

if __name__ == "__main__":
    main()
