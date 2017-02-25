import bpy
import threading
import time
import serial

gvar = 2

class CounterService(threading.Thread):


    def run(self):
        print('sdf')
        while true:
            gvar += 1
            self._counter += 1
            HelloWorldPanel.cnt += 1
            time.sleep(1)


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
        
        thread = threading.Thread(target = HelloWorldPanel.inc, args = (self, ))
        thread.start()
        
        bpy.types.Panel.__init__(self)

    def draw(self, context):
        self.layout.label(text="Hello World {0}".format(self.cnt))


def register():
    #service = CounterService()
    #service.start()
    
    #HelloWorldPanel.service = service
    bpy.utils.register_class(HelloWorldPanel)
    
    #gvar = 10

def unregister():
    service = CounterService(HelloWorldPanel)
    service.srart()

    bpy.utils.unregister_class(HelloWorldPanel)
    
if __name__ == "__main__":
    register()
    #unregister()
