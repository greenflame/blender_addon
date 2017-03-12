import bpy
import threading
import time
import serial
import sys

class HelloWorldPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_hello_world"
    bl_label = "Hello World"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def inc(self):
        while True:
            self.cnt += 1
            time.sleep(1)
    
    def __init__(self):
        self.cnt = 1
        print("test")
                
        bpy.types.Panel.__init__(self)

    def draw(self, context):
        self.layout.label(text="Hello World {0}".format(self.cnt))
        self.layout.operator("hello.hello", text='Ciao').country = "Italy"



class OBJECT_OT_HelloButton(bpy.types.Operator):
    bl_idname = "hello.hello"
    bl_label = "Say Hello"
    country = bpy.props.StringProperty()
 
    def execute(self, context):
        
        
        ser = serial.Serial(
            port='/dev/tty.wchusbserialfd120',
            baudrate=250000
        )

        print(ser.isOpen())

        ser.write("G28\n".encode('utf-8'))
        ser.close()
#        ser.write_line("G28")
        #print(ser.readstring())
        
        if self.country == '':
            print("Hello world!")
        else:
            print("Hello world from %s!" % self.country)
        return{'FINISHED'}
    
        
if __name__ == "__main__":
    bpy.utils.register_module(__name__)
