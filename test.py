# test.py
"""
Скрипт для подключения к VMware и выполнения команд в гостевой ОС виртуальной машины.

Функциональность:
- Подключение к VMware-инфраструктуре
- Выполнение пользовательских команд в указанной виртуальной машине
- Обработка ошибок соединения и выполнения команд
"""

from modules.vmware_connector import VMwareConnector
import sys


def main():
    """
    Основная функция скрипта.

    Последовательно выполняет:
    1. Инициализацию и подключение к VMware
    2. Получение имени целевой виртуальной машины от пользователя
    3. Выполнение команды в гостевой ОС
    4. Вывод результата выполнения команды
    5. Отключение от VMware

    Raises:
        Exception: Перехватывает и выводит ошибки подключения/выполнения команд
    """
    connector = VMwareConnector()
    
    try:
        # Подключение к VMware
        print("🔌 Подключение к VMware...")
        connector.connect()
        
        # Запрос имени виртуальной машины
        vm_name = input("Введите имя виртуальной машины: ").strip()
        if not vm_name:
            print("❌ Имя виртуальной машины не указано!")
            return
            
        # Проверка существования VM (дополнительная защита)
        if not connector.vm_exists(vm_name):
            print(f"❌ Виртуальная машина '{vm_name}' не найдена!")
            return
            
        # Выполнение команды в гостевой ОС
        command = input("\nВведите команду для выполнения (например 'uptime df -h'): ").strip()
        if not command:
            command = "uptime && df -h"  # Команда по умолчанию
            
        print(f"\n▶️ Выполняется команда: {command}")
        
        stdout = connector.execute_guest_command(vm_name, command)
        print("\n📊 Результат:")
        print(stdout)
            
    except ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
    except PermissionError as e:
        print(f"🔒 Ошибка доступа: {e}")
    except Exception as e:
        print(f"⚠️ Непредвиденная ошибка: {e}")
    finally:
        # Отключение
        print("🔌 Отключение от VMware...")
        connector.disconnect()

if __name__ == "__main__":
    main()