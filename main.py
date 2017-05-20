import bpy
import threading
import time
import serial
import sys
import time
import subprocess


class Config:
    port = '/dev/tty.wchusbserialfd120'
    baudrate = 250000

    slicer = '/Applications/Slic3r.app/Contents/MacOS/slic3r'
    tempPath = '/Users/alexander/Desktop/'

    tempMesh = tempPath + 'mesh.obj'
    tempCode = tempPath + 'mesh.gcode'
    
    detailedLog = False

class HelloService:

    def greet():
        print('hello, world')

class SlicerService:

    def save():
        bpy.ops.export_scene.obj(filepath=Config.tempMesh, use_selection=True)

    def slice():
        args = [Config.slicer, Config.tempMesh]
        res = subprocess.run(args, stdout=subprocess.PIPE).stdout.decode('utf-8')

        if Config.detailedLog:
            print(res)
        
    def load():
        res_file = open(Config.tempCode, 'r')
        gcode = res_file.read()
        res_file.close()
        
        SlicerService.data = gcode

class PreviewService:

    def parseMovements(gcode):
        ret = []

        for line in gcode.split('\n'):
            line = line.lower()
            line = line.split(';')[0]

            args = line.split(' ')

            if len(args) == 0:
                continue

            if args[0] != 'g0' and args[0] != 'g1':
                continue

            movement = {}

            print(line)
            for arg in args[1:]:
                if len(arg) < 2:
                    continue

                movement[arg[0]] = float(arg[1:])

            ret.append(movement)

        return ret

    def generate():
        movements = PreviewService.parseMovements(SlicerService.data)
        print(movements)

    def clear():
        return

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


class MagicService:
    
    def do_magic():
        print('Greeting..')
        HelloService.greet()

        print('Saving mesh..')
        SlicerService.save()
        print('Slicing mesh..')
        SlicerService.slice()
        print('Loading gcode..')
        SlicerService.load()
        
        print('Generating preview..')
        PreviewService.generate()

        return
    
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
        self.layout.operator('slicer.load')


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


class OBJECT_OT_Load(bpy.types.Operator):
    bl_idname = 'slicer.load'
    bl_label = 'Load'

    def execute(self, context):
        SlicerService.load()
        return{'FINISHED'}

# Preview

class PreviewPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_preview_panel'
    bl_label = 'Preview Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('preview.generate')
        self.layout.operator('preview.clear')


class OBJECT_OT_Generate(bpy.types.Operator):
    bl_idname = 'preview.generate'
    bl_label = 'Generate'

    def execute(self, context):
        PreviewService.generate()
        return{'FINISHED'}


class OBJECT_OT_Clear(bpy.types.Operator):
    bl_idname = 'preview.clear'
    bl_label = 'Clear'

    def execute(self, context):
        PreviewService.clear()
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
    
# Hello

class MagicPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_magic_panel'
    bl_label = 'Magic Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        self.layout.operator('magic.do_magic')


class OBJECT_OT_DoMagic(bpy.types.Operator):
    bl_idname = 'magic.do_magic'
    bl_label = 'Do Magic'

    def execute(self, context):
        MagicService.do_magic()
        return{'FINISHED'}

# Main

if __name__ == '__main__':
    bpy.utils.register_module(__name__)
