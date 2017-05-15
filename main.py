import bpy
import threading
import time
import serial
import sys
import time
import subprocess

#/Applications/Slic3r.app/Contents/MacOS/slic3r /Users/alexander/Desktop/cube.obj


class Config:
    port = '/dev/tty.wchusbserialfd120'
    baudrate = 250000

    slicer = '/Applications/Slic3r.app/Contents/MacOS/slic3r'
    tempPath = '/Users/alexander/Desktop/'

    tempMesh = tempPath + 'mesh.obj'
    tempCode = tempPath + 'mesh.gcode'

class HelloService:

    def greet():
        print('hello, world')

class SlicerService:

    def save():
        bpy.ops.export_scene.obj(filepath=Config.tempMesh, use_selection=True)

    def slice():
        res = subprocess.run([Config.slicer, Config.tempMesh], stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(res)

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

# Hello

class HelloPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_hello_panel'
    bl_label = 'Hello Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('hello.greet')


class OBJECT_OT_Hello(bpy.types.Operator):
    bl_idname = 'hello.greet'
    bl_label = 'Greet'

    def execute(self, context):
        HelloService.greet()
        return{'FINISHED'}

# Slicer

class SlicerPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_slicer_panel'
    bl_label = 'Slicer Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('slicer.save')
        self.layout.operator('slicer.slice')


class OBJECT_OT_Save(bpy.types.Operator):
    bl_idname = 'slicer.save'
    bl_label = 'Save'

    def execute(self, context):
        SlicerService.save()
        return{'FINISHED'}


class OBJECT_OT_Slice(bpy.types.Operator):
    bl_idname = 'slicer.slice'
    bl_label = 'Slice'

    def execute(self, context):
        SlicerService.slice()
        return{'FINISHED'}

# Printer

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

# Main

if __name__ == '__main__':
    bpy.utils.register_module(__name__)
