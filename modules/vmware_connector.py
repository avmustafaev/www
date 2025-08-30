# modules/vmware_connector.py
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
import ssl
from modules.envi import Envi


class VMwareConnector:
    """
    Класс для подключения к VMware и выполнения команд в гостевых ОС
    """

    def __init__(self):
        """Инициализация подключения к VMware"""
        self.env = Envi()
        self.si = None  # Сессия подключения

    def connect(self):
        """Установка соединения с VMware"""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.verify_mode = ssl.CERT_NONE  # Отключаем проверку SSL (для теста)

            self.si = SmartConnect(
                host=self.env.vmware_ip,
                user=self.env.vmware_user,
                pwd=self.env.vmware_password,
                port=443,
                sslContext=context
            )
            print("✅ Соединение с VMware установлено")
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения к VMware: {str(e)}")

    def disconnect(self):
        """Закрытие соединения"""
        if self.si:
            Disconnect(self.si)
            print("🔌 Соединение с VMware закрыто")

    def _get_vm_by_name(self, vm_name):
        """Находит VM по имени"""
        content = self.si.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )

        for vm in container.view:
            if vm.name == vm_name:
                return vm
        raise ValueError(f"ВМ с именем '{vm_name}' не найдена")

    def execute_guest_command(self, vm_name, command):
        """
        Выполняет команду в гостевой ОС
        Args:
            vm_name: имя виртуальной машины
            command: команда для выполнения
        Returns:
            stdout: вывод команды
        """
        try:
            vm = self._get_vm_by_name(vm_name)
            guest_ops = vm.guestOperationsManager

            # Проверка наличия гостевой ОС
            if not vm.guest or not vm.guest.toolsRunningStatus == "guestToolsRunning":
                raise RuntimeError("Гостевая ОС не запущена или VMware Tools не активны")

            # Создание файла с командой
            file_path = "/tmp/remote_command.sh"
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

            # Ожидание завершения
            while True:
                processes = guest_ops.processManager.ListProcessesInGuest(vm, [process_id])
                if not processes[0].endTime:
                    time.sleep(1)
                else:
                    break

            # Чтение вывода
            stdout = guest_ops.processManager.ReadGuestProcessConsoleOutput(
                vm=vm,
                pid=process_id,
                maxLines=1000
            ).stdout

            # Очистка
            guest_ops.fileManager.DeleteFileInGuest(vm, name=file_path)

            return stdout

        except vmodl.MethodFault as error:
            raise RuntimeError(f"Ошибка VMware API: {error.msg}")
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения команды: {str(e)}")

    def get_guest_file_content(self, vm_name, file_path):
        """
        Получает содержимое файла из гостевой ОС
        Args:
            vm_name: имя виртуальной машины
            file_path: путь к файлу в гостевой ОС
        Returns:
            содержимое файла
        """
        try:
            vm = self._get_vm_by_name(vm_name)
            guest_ops = vm.guestOperationsManager

            if not vm.guest or not vm.guest.toolsRunningStatus == "guestToolsRunning":
                raise RuntimeError("Гостевая ОС не запущена или VMware Tools не активны")

            return guest_ops.fileManager.ReadTextFileInGuest(vm, name=file_path)

        except vmodl.MethodFault as error:
            raise RuntimeError(f"Ошибка VMware API: {error.msg}")
        except Exception as e:
            raise RuntimeError(f"Ошибка чтения файла: {str(e)}")
