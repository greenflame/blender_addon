import bpy
import bmesh

import os
import threading
import time
import serial
import sys
import time
import subprocess
import random


class Config:
    port = '/dev/tty.wchusbserialfa130'
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
        try:
            os.remove(Config.tempMesh)
        except:
            pass
        bpy.ops.export_scene.obj(filepath=Config.tempMesh, use_selection=True, global_scale=10, use_triangles=True)

    def slice():
        try:
            os.remove(Config.tempCode)
        except:
            pass
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
        #print(movements)
        
        me = bpy.data.meshes.new('preview')
        ob = bpy.data.objects.new('preview', me)
        
        scn = bpy.context.scene
        scn.objects.link(ob)
        
        bm = bmesh.new()

        prev_vert = None
        cur_pos = { 'x': 0, 'y' : 0, 'z' : 0 }
        
        for movement in movements:
            for arg in movement:
                if arg in ['x', 'y', 'z']:
                    cur_pos[arg] = movement[arg]

            pos_arr = [cur_pos['x'], cur_pos['y'], cur_pos['z']]
            cur_vert = bm.verts.new(pos_arr)
            
            if 'e' in movement and prev_vert != None:
                bm.edges.new([prev_vert, cur_vert])
                
            prev_vert = cur_vert
            
            print(pos_arr)
            
        bm.to_mesh(me)
        bm.free()

    def clear():
        return

class PrinterService:

    code = None
    code_ptr = None

    cmd_sent = None
    cmd_acknowledged = None

    def connect():
        PrinterService.serial = serial.Serial(port=Config.port, baudrate=Config.baudrate, timeout=0)

    def disconnect():
        PrinterService.serial.close()
        del PrinterService.serial

    def status():
        if hasattr(PrinterService, 'serial') and PrinterService.serial.isOpen:
            return 'Connected'
        else:
            return 'Disconnected'

    def home():
        PrinterService.serial.write('G28\n'.encode())
        # PrinterService.serial.write(';G1 X90.6 Y103.8\n'.encode())
        # PrinterService.serial.write('G1 X50.6 Y53.8\n'.encode())

    def print_init():
        PrinterService.code = SlicerService.data.split('\n')
        PrinterService.code_ptr = 0
        PrinterService.cmd_sent = 0
        PrinterService.cmd_acknowledged = 0

        code = ''

        for i in range(100):
            code += 'G1 X90.6 Y103.8\n'
            code += 'G1 X50.6 Y53.8\n'

        PrinterService.code = code.split('\n')
        PrinterService.countdown = 5

    def print():

        # find next command
        next_cmd = PrinterService.code[PrinterService.code_ptr]

        # while PrinterService.code_ptr < len(PrinterService.code) and next_cmd == None:
        #     cur_str = PrinterService.code[PrinterService.code_ptr]
        #     skip = False

        #     if len(cur_str) < 1:
        #         skip = True

        #     if not skip and cur_str[0] == ';':
        #         skip = True

        #     PrinterService.code_ptr += 1

        #     if not skip:
        #         next_cmd = cur_str

        # if next_cmd == None:    # no next commmand, interrupt
        #     return False

        # read input and count acknowledgements
        data = PrinterService.serial.read(1000)
        if len(data) != 0:
            data_decoded = data.decode()
            print(data_decoded)

            cur_ack = 0

            for line in data_decoded.split('\n'):
                if line == 'ok':
                    cur_ack += 1

            print('current acknowledgements: ' + str(cur_ack))
            PrinterService.cmd_acknowledged += cur_ack
            print('ts: ' + str(PrinterService.cmd_sent))
            print('ta: ' + str(PrinterService.cmd_acknowledged))

        if PrinterService.countdown != 0:
            print('cntdwn ' + str(PrinterService.countdown))
            PrinterService.countdown -= 1
            return True

        if PrinterService.cmd_sent == PrinterService.cmd_acknowledged:
            PrinterService.serial.write((next_cmd + '\n').encode())
            print('cmd sent ' + next_cmd)
            PrinterService.cmd_sent += 1
            PrinterService.code_ptr += 1

        return True


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
        self.layout.operator('printer.print')


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

class OBJECT_OT_PrinterPrint(bpy.types.Operator):
    bl_idname = 'printer.print'
    bl_label = 'Printer Print'

    _timer = None

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_timer(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if not PrinterService.print():
                print('printing finished')
                return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        PrinterService.print_init()
        self.register_timer(context)
        return {'RUNNING_MODAL'}

    def register_timer(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(1, context.window)
        wm.modal_handler_add(self)

    def cancel_timer(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

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
