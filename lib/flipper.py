'''
Flip Dot controller running on ESP32-S3
Uses breakout board to 3x 7406 with
original Gulton Luminator decoder/driver
5 characters per module, each character is 5x7 dots


Author: Derek Kuraitis
Email:diverge@protonmail.com
'''

try:
    from time import sleep_ms  # sleep_ms is part of MicroPython
    from machine import Pin
except ImportError:
    # Define a mock Pin class here for local testing if machine.Pin is not available
    from mock_machine import sleep_ms, MockPin as Pin
    class Pin:
        IN = 0
        OUT = 1
        PULL_UP = 2
        PULL_DOWN = 3

        def __init__(self, pin_number, mode, pull=None):
            self.pin_number = pin_number
            self.mode = mode
            self.pull = pull

        def on(self):
            pass

        def off(self):
            pass


class Display:
    
    dot_row=[9,8,18,17] #gpio pins assigned to rows (x)
    dot_column=[14,13,12,11,10] #gpio pins assigned to column (y)
    col_pin = []
    row_pin = []

    def __init__(self,modules = None):
        self.modules = modules #how many self.modules wired (pwb bits)
        if modules == None:
            print("Running on PC: Setting up Pins")
        else:
            for i in range(len(self.dot_column)):
                self.col_pin.append(Pin(self.dot_column[i], mode=Pin.OUT,pull=Pin.PULL_DOWN))
            for i in range(len(self.dot_row)):
                self.row_pin.append(Pin(self.dot_row[i], mode=Pin.OUT,pull=Pin.PULL_DOWN))


            self.pwb_2_0 = Pin(16, mode=Pin.OUT, pull=Pin.PULL_DOWN)
            self.pwb_2_1 = Pin(15, mode=Pin.OUT, pull=Pin.PULL_DOWN)
            self.sign_2_0 = Pin(7, mode=Pin.OUT, pull=Pin.PULL_DOWN)
            self.sign_2_1 = Pin(6, mode=Pin.OUT, pull=Pin.PULL_DOWN)
            self.sign_2_2 = Pin(5, mode=Pin.OUT, pull=Pin.PULL_DOWN)

            self.erase_pin = Pin(37,mode=Pin.OUT, pull=Pin.PULL_DOWN)
            self.write_pin = Pin(36,mode=Pin.OUT, pull=Pin.PULL_DOWN)

    #only flip dots needed based on previous display
    display_buffer1 = [0 for i in range(7)] 
    display_buffer2 = [0 for i in range(7)]

    flip_ms = 3 #1-10ms is ok. Longer will heat up coils

    stop_draw = 0 #change to 1 to stop on_off()

    #test characters
    checker1_char = [
        0b10101,
        0b01010,
        0b10101,
        0b01010,
        0b10101,
        0b01010,
        0b10101
        ]

    checker2_char = [
        0b01010,
        0b10101,
        0b01010,
        0b10101,
        0b01010,
        0b10101,
        0b01010,
        ]


    #keeps erasing and writing dots separate to prevent mistakes
    def flip_off(self):
        '''
        flips dot to 'off'
        '''
        self.erase_pin.on()
        sleep_ms(self.flip_ms)
        self.erase_pin.off()

    def flip_on(self):
        '''
        flips dot to 'on'
        '''
        #flips dot to 'on"
        self.write_pin.on()
        sleep_ms(self.flip_ms)
        self.write_pin.off()

    def draw_dot(self,x:int,y:int,z:int,write:bool):
        """
        flips individual dots
        x=column(max 25),y=row(max 7),z=module(max 3)
        write=true:yellow,false:black
        """
        if self.modules == None:
            print("dot_configure() Must be called from Esp32")
            return

        i = 0
        if z == 0:
            self.pwb_2_0.off()
            self.pwb_2_1.off()
        elif z == 1:
            self.pwb_2_0.on()
            self.pwb_2_1.off()
        else:
            self.pwb_2_0.off()
            self.pwb_2_1.on()
        for a in range(4):
            if y % 2:
                self.row_pin[i].on()
                y //= 2
                i += 1
            else:
                self.row_pin[i].off()
                y //= 2
                i += 1
        i = 0
        for b in range(5):
            if x % 2:
                self.col_pin[i].on()
                x //= 2
                i += 1
            else:
                self.col_pin[i].off()
                x //= 2
                i += 1
        if write:
            self.flip_on()
        else:
            self.flip_off()

    def write_dot_to_buffer(self,x:int,y:int,write:bool):

        if write:
            if not(self.display_buffer1[y] & (1 << x)):
                self.display_buffer1[y] = self.display_buffer1[y] + (1 << x)

        else:
            if self.display_buffer1[y] & (1 << x):
                self.display_buffer1[y] = self.display_buffer1[y] - (1 << x)


    def draw_row(self,row:int,i:int):

        '''Draws row to display'''

        if self.modules is None:
            print("draw_row() must be called from ESP32")
            return

        for z in range(self.modules):
            x = 0
            #print(str(z))
            for a in range(25):
                if row % 2:
                    self.draw_dot(x,i,z,True)
                    row //= 2
                    x += 1
                else:
                    self.draw_dot(x,i,z,False)
                    row //= 2
                    x += 1

    def write_row_fast(self,rowbyte:int,i:int):

        x = 0
        buff = self.display_buffer1[i]

        while rowbyte or buff:
            #print(len(dot_column))
            if (rowbyte % 2) and (rowbyte % 2 != buff % 2):
                #print("write " + str(rowbyte%2) + " -> "+ str(buff%2))
                self.write_dot_to_buffer(x,i,True)
                rowbyte //= 2
                buff //= 2
                self.display_buffer1[i] += 1<<x
                x += 1
            elif (not rowbyte % 2) and (rowbyte % 2 != buff % 2):
                #print("erase " + str(rowbyte%2) + " -> "+ str(buff%2))
                self.write_dot_to_buffer(x,i,False)
                rowbyte //= 2
                buff //= 2
                self.display_buffer1[i] -= 1<<x
                x += 1
            elif (rowbyte % 2) and (rowbyte % 2 == buff % 2):
                #print("1 same")
                rowbyte //= 2
                buff //= 2
                x += 1
            else:
                #print("0 same")
                rowbyte //= 2
                buff //=2
                x += 1

    def write_row_to_buffer(self,rowbyte:int,i:int):
        x = 0
        buff = self.display_buffer1[i]

        while rowbyte or buff:
            if (rowbyte % 2) and (rowbyte % 2 != buff % 2):
                #print("write " + str(rowbyte%2) + " -> "+ str(buff%2))
                self.draw_dot(x,i,0,True)
                rowbyte //= 2
                buff //= 2
                self.display_buffer1[i] += 1<<x
                x += 1
            elif (not rowbyte % 2) and (rowbyte % 2 != buff % 2):
                #print("erase " + str(rowbyte%2) + " -> "+ str(buff%2))
                self.draw_dot(x,i,0,False)
                rowbyte //= 2
                buff //= 2
                self.display_buffer1[i] -= 1<<x
                x += 1
            elif (rowbyte % 2) and (rowbyte % 2 == buff % 2):
                #print("1 same")
                rowbyte //= 2
                buff //= 2
                x += 1
            else:
                #print("0 same")
                rowbyte //= 2
                buff //=2
                x += 1
    '''
    def draw_column(column_byte:int,i:int):
        x = 0

        for a in range(7):
            if row % 2:
                dot_configure(x,i,True)
                row //= 2
                x += 1
            else:
                dot_configure(x,i,False)
                row //= 2
                x += 1
    '''
    def draw_character(self,dot_char:bytes, pos:int):
        for i in range(7):
            print("dot character before:" + str(dot_char[i]))
            self.draw_row( (dot_char[i] << (5 * pos)) , i)

    def draw_character_fast(self,dot_char:bytes, pos:int):
        if pos > 4:
            print("pos too high")
            return
        for i in range(7):
            self.write_row_fast((dot_char[i] << (5 * pos)) , i)

    def write_character_to_buffer(self,character_byte:bytes, position:int):
        '''draws a single '''
        if position > ((self.modules * 5) - 1):
            print("position too high")
            return
        x = 0
        for i in range(7):
            row_byte = character_byte[i]
            for a in range(5):
                if row_byte % 2:
                    #print("1" , end = "")
                    self.write_dot_to_buffer(((position*5) + a),i,True)
                    row_byte //= 2
                else:
                    #print("0" , end = "")
                    self.write_dot_to_buffer(((position*5) + a),i,False)
                    row_byte //= 2
            #print("x: " + str(x))

    def show(self):
        '''draws a row from the buffer to display'''
        if self.modules == None:
            print("show() must be called from Esp32")
            return
        for y in range(7):
            row_from_buff = self.display_buffer1[y]
            row_to_buff = self.display_buffer2[y]
            for z in range(self.modules):
                #print(str(z))
                for x in range(25):
                    if (row_from_buff % 2) and (row_from_buff % 2 != row_to_buff % 2):
                        self.draw_dot(x,y,z,True)
                        row_from_buff //= 2
                        row_to_buff //= 2
                        x += 1
                    elif (not row_from_buff % 2) and (row_from_buff % 2 != row_to_buff % 2):
                        self.draw_dot(x,y,z,False)
                        row_from_buff //= 2
                        row_to_buff //= 2
                        x += 1
                    elif (row_from_buff % 2) and (row_from_buff % 2 == row_to_buff % 2):
                        row_from_buff //= 2
                        row_to_buff //= 2
                        x += 1
                    else:
                        row_from_buff //= 2
                        row_to_buff //=2
                        x += 1
        for i in range(7):
            self.display_buffer2[i] = self.display_buffer1[i]

    def row_on_off(self):
        '''use as test. draws a row, erases and moves on to the next'''
        if self.modules == None:
            print("row_on_off() must run from ESP32")
            return

        while not self.stop_draw:
            for i in range(7):
                self.draw_row(0b1111111111111111111111111,i)
                self.draw_row(0,i)

    def write_string_to_buffer(self,input_string:str,font:list):
        '''draws a string to buffer from font list'''
        for i in range(len(input_string)):
            in_char = ord(input_string[i])
            self.write_character_to_buffer(font[in_char],i)

    def fill(self, color:int):
        '''0 for black, 1 for yellow'''

        self.display_buffer1 = [
            ((1 << (color*25*(1 if self.modules == None else self.modules)))-1)
            for i in range(7)]

    def clear_display_force(self):
        '''flips every dot to off'''
        for i in range(7):
            self.draw_row(0,i)
    #_thread.start_new_thread(on_off,())
    #draw_character(checker1_char,1)

