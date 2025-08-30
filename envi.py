# modules/envi.py
import os
from dotenv import load_dotenv


class Envi:
    """
    Класс для загрузки и управления переменными окружения из файла .env
    """

    def __init__(self):
        """Загружает переменные окружения из файла .env"""
        load_dotenv()  # Загрузка .env в os.environ

        # Обязательные переменные
        self.vmware_ip = os.getenv("VMWARE_IP")
        self.vmware_user = os.getenv("VMWARE_USER")
        self.vmware_password = os.getenv("VMWARE_PASSWORD")
        self.vm_root_user = os.getenv("VM_ROOT_USER")
        self.vm_root_password = os.getenv("VM_ROOT_PASSWORD")

        self._validate()  # Проверка наличия обязательных переменных

    def _validate(self):
        """Проверяет наличие всех обязательных переменных"""
        missing = [var for var in [
            self.vmware_ip, self.vmware_user, self.vmware_password,
            self.vm_root_user, self.vm_root_password
        ] if not var]

        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {missing}")

    def get_vmware_config(self):
        """Возвращает конфиг для подключения к VMware"""
        return {
            "ip": self.vmware_ip,
            "user": self.vmware_user,
            "password": self.vmware_password
        }

    def get_vm_root_credentials(self):
        """Возвращает root-доступ к виртуальной машине"""
        return {
            "username": self.vm_root_user,
            "password": self.vm_root_password
        }
