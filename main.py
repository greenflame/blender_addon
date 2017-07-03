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

# Slicer

class SlicerPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_slicer_panel'
    bl_label = 'Slicer Panel'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):        
        layout = self.layout
        scn = bpy.context.scene
        
        layout.prop(scn, 'SlicerPath')
        layout.separator()
        
        layout.label("Extruder:")
        layout.prop(scn, 'NozzleDiameter')
        layout.separator()
        layout.prop(scn, 'UseRetraction')
        layout.prop(scn, 'RetractionDistance')
        layout.prop(scn, 'RetractionSpeed')
        layout.separator()
        
        layout.label("Layer:")
        layout.prop(scn, 'LayerHeight')
        layout.separator()
        layout.prop(scn, 'TopSolidLayers')
        layout.prop(scn, 'BottomSolidLayers')
        layout.prop(scn, 'OutlineShells')
        layout.separator()

        layout.label("Infill:")
        layout.prop(scn, 'InfillPrecentage')
        layout.prop(scn, 'FillPattern')
        layout.separator()

        layout.label("Temperature:")
        layout.prop(scn, 'ExtruderTemperature')
        layout.prop(scn, 'BedTemperature')
        layout.separator()
        
        layout.label("Motion:")
        layout.prop(scn, 'PrintingSpeed')
        layout.prop(scn, 'AvoidCrossingMovements')
        layout.separator()
        
        layout.operator('slicer.slice')


class OBJECT_OT_Save(bpy.types.Operator):
    bl_idname = 'slicer.save'
    bl_label = 'Save'

    def execute(self, context):
        SlicerService.save()
        return{'FINISHED'}


class OBJECT_OT_Slice(bpy.types.Operator):
    bl_idname = 'slicer.slice'
    bl_label = 'Slice Selected Model'

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
        layout = self.layout
        scn = bpy.context.scene

        layout.label("State:")
        layout.prop(scn, 'PreviewStart')
        layout.prop(scn, 'PreviewEnd')
        layout.separator()
        
        layout.label("Live Preview:")
        layout.prop(scn, 'LivePreviewTracking')
        layout.prop(scn, 'LivePreviewUpdateInterval')
        layout.separator()
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("preview.generate")
        row.operator("preview.clear")
        

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
        layout = self.layout
        scn = bpy.context.scene

        layout.label('Connection:')
        layout.prop(scn, 'SerialPort')
        layout.prop(scn, 'BaudRate')
        layout.label('Connection status: ok')        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("printer.connect")
        row.operator("printer.disconnect")
        layout.separator()

        layout.label('Temperature:')
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(scn, 'ExtruderTemperatureAim')
        row.label('Current: 207°C')
        
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.prop(scn, 'BedTemperatureAim')
        row.label('Current: 103°C')
        
        layout.separator()

        layout.label('Override Settings:')
        layout.prop(scn, 'MovementOverride')
        layout.prop(scn, 'ExtrusionOverride')
        layout.separator()        
        
        layout.label('Printing progress: 36% finished, 22min left')
        self.layout.operator('printer.home')
        row = layout.row(align=True)
        row.alignment = 'EXPAND'
        row.operator("printer.print")
        row.operator("printer.pause")
        row.operator("printer.stop")


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
    bl_label = 'Home All Axes'

    def execute(self, context):
        PrinterService.home()
        return{'FINISHED'}
    
class OBJECT_OT_PrinterPause(bpy.types.Operator):
    bl_idname = 'printer.pause'
    bl_label = 'Pause'

    def execute(self, context):
#        PrinterService.home()
        return{'FINISHED'}

class OBJECT_OT_PrinterStop(bpy.types.Operator):
    bl_idname = 'printer.stop'
    bl_label = 'Stop'

    def execute(self, context):
        PrinterService.home()
        return{'FINISHED'}

class OBJECT_OT_PrinterPrint(bpy.types.Operator):
    bl_idname = 'printer.print'
    bl_label = 'Print'

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
    
# Prop test

class MyAddonProperties(bpy.types.PropertyGroup):
    my_prop_1 = bpy.props.IntProperty()
    my_prop_2 = bpy.props.IntProperty()
    my_prop_3 = bpy.props.IntProperty()


bl_info = { 
    "name":     "Render ISO", 
    "category": "Render"  # perhaps wrong
}

class RenderIsoOperator(bpy.types.Operator):
    ''' An example operator for addon '''
    bl_idname = "render.render_iso"
    bl_label  = "Render ISO"
    bl_options = {'REGISTER'}

    tile_width = bpy.props.IntProperty(
        name="Tile width",
        min=10,
        max=1000
    )

    def execute(self, context):
        obj = context.scene.objects.active
        # Do the rendering here
        return {"FINISHED"}


class RenderIsoPanel(bpy.types.Panel):
    bl_idname = "RENDER_PT_render_iso"
    bl_label = "Render ISO"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        op = layout.operator(RenderIsoOperator.bl_idname)
        op.tile_width = scene.iso_render.tile_width
        layout.prop(scene.iso_render, "tile_width")

class IsoRenderSettings(bpy.types.PropertyGroup):
    tile_width = bpy.props.IntProperty(
        name="Tile width",
        min=0,
        max=1000
    )

# Main

def initProps():
    scn = bpy.context.scene
    
    # Slicer
    
    bpy.types.Scene.SlicerPath = bpy.props.StringProperty(
        name = "Slicer Path", 
        description = "Path to your slicer executable")
    bpy.context.scene['SlicerPath'] = '/Applications/Slic3r.app/Contents/MacOS/slic3r'

    bpy.types.Scene.NozzleDiameter = bpy.props.FloatProperty(
        name = "Nozzle Diameter", 
        description = "The diameter of your extruder nozzle, mm")
    bpy.context.scene['NozzleDiameter'] = 0.4

    bpy.types.Scene.UseRetraction = bpy.props.BoolProperty(
        name = "Use retraction", 
        description = "Reverse filament direction at the end of a loop to help prevent stringing")
    bpy.context.scene['UseRetraction'] = True
    
    bpy.types.Scene.RetractionDistance = bpy.props.FloatProperty(
        name = "Retraction Distance",
        description = "mm")
    bpy.context.scene['RetractionDistance'] = 4.0

    bpy.types.Scene.RetractionSpeed = bpy.props.FloatProperty(
        name = "Retraction Speed",
        description = "mm/s")
    bpy.context.scene['RetractionSpeed'] = 30.0
    
    bpy.types.Scene.LayerHeight = bpy.props.FloatProperty(
        name = "Layer Height",
        description = "mm")
    bpy.context.scene['LayerHeight'] = 0.4
    
    bpy.types.Scene.TopSolidLayers = bpy.props.IntProperty(
        name = "Top Solid Layers",
        description = "")
    bpy.context.scene['TopSolidLayers'] = 3
    
    bpy.types.Scene.BottomSolidLayers = bpy.props.IntProperty(
        name = "Bottom Solid Layers",
        description = "")
    bpy.context.scene['BottomSolidLayers'] = 2
    
    bpy.types.Scene.OutlineShells = bpy.props.IntProperty(
        name = "Outline Shells",
        description = "")
    bpy.context.scene['OutlineShells'] = 2
    
    bpy.types.Scene.InfillPrecentage = bpy.props.IntProperty(
        name = "Infill Precentage",
        description = "%")
    bpy.context.scene['InfillPrecentage'] = 30
    
    bpy.types.Scene.FillPattern = bpy.props.EnumProperty(
        #(identifier, name, description, icon, number)
        items = [('Triangular', 'Triangular', ""), 
                 ('Rectlinear', 'Rectlinear', ""),
                 ('Grid', 'Grid', ""),
                 ('FastHoneycomb', 'Fast Honeycomb', ""),
                 ('FullHoneycomb', 'Full Honeycomb', "")],
        name = "Fill Pattern")
    scn['FillPattern'] = 'FastHoneycomb'

    bpy.types.Scene.ExtruderTemperature = bpy.props.IntProperty(
        name = "Extruder Temperature",
        description = "°C")
    bpy.context.scene['ExtruderTemperature'] = 210
    
    bpy.types.Scene.BedTemperature = bpy.props.IntProperty(
        name = "Bed Temperature",
        description = "°C")
    bpy.context.scene['BedTemperature'] = 110
    
    bpy.types.Scene.PrintingSpeed = bpy.props.FloatProperty(
        name = "PrintingSpeed",
        description = "mm/s")
    bpy.context.scene['PrintingSpeed'] = 30.0

    bpy.types.Scene.AvoidCrossingMovements = bpy.props.BoolProperty(
        name = "Avoid crossing outline for travel movements", 
        description = "")
    bpy.context.scene['AvoidCrossingMovements'] = True
    
    #  Preview
    
    bpy.types.Scene.PreviewStart = bpy.props.FloatProperty(
        name = "PreviewStart",
        description = "%")
    bpy.context.scene['PreviewStart'] = 0.0

    bpy.types.Scene.PreviewEnd = bpy.props.FloatProperty(
        name = "PreviewEnd",
        description = "%")
    bpy.context.scene['PreviewEnd'] = 60.0

    
    bpy.types.Scene.LivePreviewTracking = bpy.props.BoolProperty(
        name = "Live Preview Tracking", 
        description = "")
    bpy.context.scene['LivePreviewTracking'] = True
    
    bpy.types.Scene.LivePreviewUpdateInterval = bpy.props.IntProperty(
        name = "Update Interval",
        description = "sec")
    bpy.context.scene['LivePreviewUpdateInterval'] = 5

    # Printer
    
    bpy.types.Scene.SerialPort = bpy.props.EnumProperty(
        #(identifier, name, description, icon, number)
        items = [('serial1', '/dev/tty.wchusbserialfa130', ""), 
                 ('serial2', '/dev/tty.Bluetooth-Incoming-Port', "")],
        name = "Serial")
    scn['SerialPort'] = '/dev/tty.wchusbserialfa130'

    bpy.types.Scene.BaudRate = bpy.props.EnumProperty(
        #(identifier, name, description, icon, number)
        items = [('br1', '9600', ""), 
                 ('br2', '115200', ""),
                 ('br3', '250000', "")],
        name = "Baud Rate")
    scn['BaudRate'] = 'br3'

    bpy.types.Scene.ExtruderTemperatureAim = bpy.props.IntProperty(
        name = "Extruder",
        description = "sec")
    bpy.context.scene['ExtruderTemperatureAim'] = 210

    bpy.types.Scene.BedTemperatureAim = bpy.props.IntProperty(
        name = "Bed",
        description = "sec")
    bpy.context.scene['ExtruderTemperatureAim'] = 210

    bpy.types.Scene.MovementOverride = bpy.props.IntProperty(
        name = "Movement",
        description = "sec")
    bpy.context.scene['ExtruderTemperatureAim'] = 90

    bpy.types.Scene.ExtrusionOverride = bpy.props.IntProperty(
        name = "Extrusion",
        description = "sec")
    bpy.context.scene['ExtrusionOverride'] = 110

if __name__ == '__main__':
    initProps()
    bpy.utils.register_module(__name__)
    bpy.types.Scene.iso_render = bpy.props.PointerProperty(type=IsoRenderSettings)
