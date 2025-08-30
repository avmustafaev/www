# modules/vmware_connector.py
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
from modules.envi import Envi
import time
import uuid
import logging


class VMwareConnector:
    """
    Класс для подключения к VMware и выполнения команд в гостевых ОС
    """

    def __init__(self):
        """Инициализация подключения к VMware"""
        self.env = Envi()
        self.si = None  # Сессия подключения
        self._logger = logging.getLogger(__name__)

    def connect(self, verify_ssl=False):
        """
        Установка соединения с VMware
        Args:
            verify_ssl: Флаг проверки SSL-сертификатов (по умолчанию False)
        """
        try:
            context = ssl.create_default_context() if verify_ssl else ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = verify_ssl
            context.verify_mode = ssl.CERT_REQUIRED if verify_ssl else ssl.CERT_NONE

            self.si = SmartConnect(
                host=self.env.vmware_ip, 
                user=self.env.vmware_user, 
                pwd=self.env.vmware_password, 
                port=443,
                sslContext=context
            )
            self._logger.info("✅ Соединение с VMware установлено")
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения к VMware: {str(e)}")

    def disconnect(self):
        """Закрытие соединения"""
        if self.si:
            Disconnect(self.si)
            self._logger.info("🔌 Соединение с VMware закрыто")

    def _check_tools_status(self, vm):
        """Проверяет статус VMware Tools"""
        if not vm.guest or not vm.guest.toolsRunningStatus == "guestToolsRunning": 
            raise RuntimeError("Гостевая ОС не запущена или VMware Tools не активны")

    def _get_vm_by_name(self, vm_name):
        """Находит VM по имени"""
        content = self.si.RetrieveContent() 
        container = content.viewManager.CreateContainerView( 
            content.rootFolder, [vim.VirtualMachine], True
        )

        try:
            for vm in container.view:
                if vm.name == vm_name:
                    return vm
            raise ValueError(f"ВМ с именем '{vm_name}' не найдена")
        finally:
            container.Destroy()  # Освобождение ресурсов

    def execute_guest_command(self, vm_name, command, timeout=30):
        """
        Выполняет команду в гостевой ОС
        Args:
            vm_name: имя виртуальной машины
            command: команда для выполнения
            timeout: максимальное время ожидания выполнения (секунды)
        Returns:
            stdout: вывод команды
        """
        try:
            vm = self._get_vm_by_name(vm_name)
            guest_ops = vm.guestOperationsManager
            self._check_tools_status(vm)

            # Генерация уникального имени файла
            file_path = f"/tmp/remote_command_{uuid.uuid4().hex}.sh"
            guest_ops.fileManager.createTextFileInGuest(
                vm=vm,
                name=file_path,
                content=f"#!/bin/bash\n{command}\nexit $?"
            )

            # Запуск команды
            process_id = guest_ops.processManager.RunProgramInGuest(
                vm=vm,
                programPath="/bin/bash",
                arguments=f"{file_path}"
            )

            # Ожидание завершения с таймаутом
            start_time = time.time()
            while time.time() - start_time < timeout:
                processes = guest_ops.processManager.ListProcessesInGuest(vm, [process_id])
                if not processes[0].endTime:
                    time.sleep(0.5)
                else:
                    break
            else:
                raise TimeoutError(f"Превышено время ожидания выполнения команды ({timeout} сек)")

            # Чтение вывода
            stdout = guest_ops.processManager.ReadGuestProcessConsoleOutput(
                vm=vm,
                pid=process_id,
                maxLines=5000  # Увеличенный размер вывода
            ).stdout

            # Очистка
            guest_ops.fileManager.DeleteFileInGuest(vm, name=file_path)

            return stdout

        except (vmodl.MethodFault, vim.fault.FileFault) as error:
            raise RuntimeError(f"Ошибка VMware API: {error.msg}")
        except Exception as e:
            # Очистка ресурсов в случае ошибки
            try:
                guest_ops.fileManager.DeleteFileInGuest(vm, name=file_path)
            except:
                pass
            raise RuntimeError(f"Ошибка выполнения команды: {str(e)}")

    def get_guest_file_content(self, vm_name, file_path, max_lines=5000):
        """
        Получает содержимое файла из гостевой ОС
        Args:
            vm_name: имя виртуальной машины
            file_path: путь к файлу в гостевой ОС
            max_lines: максимальное количество строк для чтения
        Returns:
            содержимое файла
        """
        try:
            vm = self._get_vm_by_name(vm_name)
            guest_ops = vm.guestOperationsManager
            self._check_tools_status(vm)

            return guest_ops.fileManager.ReadTextFileInGuest(vm, name=file_path, maxLines=max_lines)

        except vim.fault.FileNotFound:
            raise FileNotFoundError(f"Файл '{file_path}' не найден в гостевой ОС")
        except (vmodl.MethodFault, vim.fault.FileFault) as error:
            raise RuntimeError(f"Ошибка VMware API: {error.msg}")
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения файла: {str(e)}")
