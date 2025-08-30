# modules/envi.py
import os
from dotenv import load_dotenv


class Envi:
    """
    Класс для загрузки и управления переменными окружения из файла .env
    
    Атрибуты:
        vmware_ip (str): IP-адрес VMware
        vmware_user (str): Имя пользователя VMware
        vmware_password (str): Пароль VMware
        vm_root_user (str): Root-пользователь виртуальной машины
        vm_root_password (str): Root-пароль виртуальной машины
    """

    def __init__(self, env_path: str = ".env"):
        """Инициализация класса с загрузкой переменных окружения
        
        Args:
            env_path: Путь к файлу .env (по умолчанию ".env")
        """
        # Улучшение: возможность указания произвольного пути к .env
        load_dotenv(env_path)

        # Обязательные переменные
        self.vmware_ip = os.getenv("VMWARE_IP")
        self.vmware_user = os.getenv("VMWARE_USER")
        self.vmware_password = os.getenv("VMWARE_PASSWORD")
        self.vm_root_user = os.getenv("VM_ROOT_USER")
        self.vm_root_password = os.getenv("VM_ROOT_PASSWORD")

        self._validate()

    def _validate(self):
        """Проверяет наличие всех обязательных переменных"""
        required_vars = [
            ("VMWARE_IP", self.vmware_ip),
            ("VMWARE_USER", self.vmware_user),
            ("VMWARE_PASSWORD", self.vmware_password),
            ("VM_ROOT_USER", self.vm_root_user),
            ("VM_ROOT_PASSWORD", self.vm_root_password)
        ]
        
        # Улучшение: проверка через кортежи (имя переменной, значение)
        missing = [var_name for var_name, value in required_vars if not value]
        
        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")

    def get_vmware_config(self) -> dict:
        """Возвращает конфиг для подключения к VMware
        
        Returns:
            dict: Конфигурация соединения с VMware
        """
        return {
            "ip": self.vmware_ip,
            "user": self.vmware_user,
            "password": self.vmware_password
        }

    def get_vm_root_credentials(self) -> dict:
        """Возвращает root-доступ к виртуальной машине
        
        Returns:
            dict: Данные для root-подключения
        """
        return {
            "username": self.vm_root_user,
            "password": self.vm_root_password
        }
