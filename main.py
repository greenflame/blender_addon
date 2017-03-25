import bpy
import threading
import time
import serial
import sys
import time


class Config:
    port = '/dev/tty.wchusbserialfd120'
    baudrate = 250000

    slicer = '/Applications/Slic3r.app/Contents/MacOS/slic3r'


class PrinterService:

    def connect():
        PrinterService.serial = serial.Serial(Config.port, Config.baudrate)

    def disconnect():
        PrinterService.serial.close()
        del PrinterService.serial

    def status():
        if hasattr(PrinterService, 'serial') and PrinterService.serial.isOpen:
            return 'Connected'
        else:
            return 'Disconnected'

    def home():
        PrinterService.serial.write('G28\n'.encode('utf-8'))


class SlicerService:
    q = 1


class HelloPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_hello_panel'
    bl_label = 'Hello Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('hi.hello')


class OBJECT_OT_HelloButton(bpy.types.Operator):
    bl_idname = 'hi.hello'
    bl_label = 'Say Hello'

    def execute(self, context):
        print('Hello world!')
        return{'FINISHED'}


class PrinterPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_printer_panel'
    bl_label = 'Printer Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('printer.connect')
        self.layout.operator('printer.disconnect')
        self.layout.operator('printer.status')
        self.layout.operator('printer.home')


class OBJECT_OT_PrinterConnect(bpy.types.Operator):
    bl_idname = 'printer.connect'
    bl_label = 'Printer Connect'

    def execute(self, context):
        PrinterService.connect()
        return{'FINISHED'}


class OBJECT_OT_PrinterDisconnect(bpy.types.Operator):
    bl_idname = 'printer.disconnect'
    bl_label = 'Printer Disconnect'

    def execute(self, context):
        PrinterService.disconnect()
        return{'FINISHED'}


class OBJECT_OT_PrinterStatus(bpy.types.Operator):
    bl_idname = 'printer.status'
    bl_label = 'Printer Status'

    def execute(self, context):
        print(PrinterService.status())
        return{'FINISHED'}


class OBJECT_OT_PrinterHome(bpy.types.Operator):
    bl_idname = 'printer.home'
    bl_label = 'Printer Home'

    def execute(self, context):
        PrinterService.home()
        return{'FINISHED'}


if __name__ == '__main__':
    bpy.utils.register_module(__name__)
