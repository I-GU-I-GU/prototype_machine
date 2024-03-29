from machine import Pin, UART, reset
import time
import rp2

show_debug = True

device_id = '3'
master_command = ""
execute_flag = False
running_state = 0
main_state = 0

printer_state = 0
printer_state_timer = 0

origin_flag = True
origin_state_timer = 0
origin_state = 0
#======================================================================================================
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def run_motor1():
    wrap_target()
    set(pins, 1)   [31]
    nop()
    set(pins, 0)   [31]
    nop()
    wrap()

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def run_motor2():
    wrap_target()
    set(pins, 1)   [31]
    nop()
    set(pins, 0)   [31]
    nop()
    wrap()

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def run_motor3():
    wrap_target()
    set(pins, 1)   [31]
    nop()
    set(pins, 0)   [31]
    nop()
    wrap()

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def run_motor4():
    wrap_target()
    set(pins, 1)   [31]
    nop()
    set(pins, 0)   [31]
    nop()
    wrap()

on_delay = 0
slap_up_time= 0
wait_rolling_more_time = 0
slap_down_time = 0
#======================================================================================================
parameter_file_name = 'params.txt'
try:
    params_file = open(parameter_file_name,'r')
    params_text = str(params_file.read())
    params_list = params_text.split(',')                        # on_delay, slap_up_time, slap_down_time
    on_delay = int(params_list[0])
    slap_up_time= int(params_list[1])
    wait_rolling_more_time = int(params_list[2])
    slap_down_time = int(params_list[3])
    if show_debug:
        print("init ok")
except:
    on_delay = 1500
    slap_up_time= 110
    wait_rolling_more_time =50
    slap_down_time = 65
    if show_debug:
        print("init fail")
#======================================================================================================
current_silo = 0
run_printer_flag = False
paper_test_flag = True
motor_state = 0
motor_timer = 0
# ========= assigned direction pin ===========
paper_switch_pull = Pin(22,Pin.IN,Pin.PULL_UP)
paper_switch_eject = Pin(26,Pin.IN,Pin.PULL_UP)
duo_switch = Pin(20,Pin.IN,Pin.PULL_UP)
slap_switch = Pin(27,Pin.IN,Pin.PULL_UP)
motor1_dir_pin = Pin(14,Pin.OUT)                    # paper roller motor old =====12
motor2_dir_pin = Pin(12,Pin.OUT)                    # slap motor old ===== 14

relay_slab = Pin(10,Pin.OUT)
relay_roller = Pin(11,Pin.OUT)

# motor3_dir_pin = Pin(21,Pin.OUT)
# motor4_dir_pin = Pin(27,Pin.OUT)
slap_target_pulse = 1000
# ========== debug parameters =====
debug_roller_motor_forward = False
debug_roller_motor_backward = False
debug_slap_motor_forward = False
debug_slap_motor_backward = False
debugging_timer = 0
debugging_state = 0
# ============ read parameters from text ==========

device_link = UART(0, baudrate=9600, bits=8, parity=None, stop=1,tx=Pin(0), rx=Pin(1),timeout=1000)
device_link.read()                                                                     # clear data in serial port buffer

motor1_controller = rp2.StateMachine(0, run_motor1, freq=2500000, set_base=Pin(15))      # old === GPIO13 => pulse, GPIO12 => direction //roller
motor2_controller = rp2.StateMachine(1, run_motor2, freq=1200000, set_base=Pin(13))      # old === GPIO15 => pulse, GPIO14 => direction //slab
#========== sub functions ==========
    
def set_dir(motor_number,direction):
    if motor_number == 1:
        motor1_dir_pin.value(direction)
    elif motor_number == 2:
        motor2_dir_pin.value(direction)
    elif motor_number == 0:
        pass
def On_slab():
    relay_slab.value(1)
    
def Off_slab():
    relay_slab.value(0)
    
def On_roller():
    relay_roller.value(1)

def Off_roller():
    relay_roller.value(0)

def off_motor():
    motor1_controller.active(0)
    motor2_controller.active(0)

def initial_io():
    motor1_dir_pin.value(0)
    motor2_dir_pin.value(0)

def resp_485(message):
    resp_message = device_id + message + "\n"
    device_link.write(bytes( ord(ch) for ch in resp_message))

def set_roller_motor_forward():     # tight paper
    motor1_dir_pin.value(1)

def set_roller_motor_backward():     # release paper
    motor1_dir_pin.value(0)

def set_slap_motor_up():
    motor2_dir_pin.value(0)

def set_slap_motor_down():
    motor2_dir_pin.value(1)

off_motor()
initial_io()
origin_flag = True

while True:
    # =========== command from master ============

    # print(slap_switch.value())
    # time.sleep(0.2)
    # print(duo_switch.value())
    # print(paper_switch_pull.value())
    # print(paper_switch_eject.value())
    if paper_test_flag == True:
        if paper_switch_pull.value() ==0:
            On_roller()
            set_roller_motor_forward()
            motor1_controller.active(1)
        elif paper_switch_eject.value() ==0:
            On_roller()
            set_roller_motor_backward()
            motor1_controller.active(1)
        elif paper_switch_eject.value() ==1 and paper_switch_pull.value() ==1 :
            Off_roller()
        else :
            pass
    else:
        pass

    if(device_link.any()):
        try:
            char_cmd = device_link.read(1)
            char_cmd = char_cmd.decode()
            if char_cmd == '\n':
                execute_flag = True
            else:
                master_command = master_command + char_cmd
        except:
            pass

    if execute_flag==True:
        # print(master_command)
        # check command
        if len(master_command) > 0:
            if master_command[0] == device_id:
                if master_command[1] == 'r':
                    message = "node" + device_id + " reset"
                    resp_485(message=message)
                    time.sleep(0.1)
                    reset()
                elif master_command[1] == 's':          # start printer operation
                    if len(master_command)>=3:
                        if master_command[2] == '1':
                            run_printer_flag = True
                            paper_test_flag = False
                            printer_state = 0
                        elif master_command[2] == '0':
                            origin_flag = True
                            paper_test_flag = False
                            origin_state = 0
                        message = "OK"
                        resp_485(message=message)

                elif master_command[1] == 'l':
                    message = str(duo_switch.value()) + "\t" + str(slap_switch.value())
                    resp_485(message=message)
                    message = ""
                elif master_command[1] == 'c':          # check printer operation
                    message = "Out of state"
                    if printer_state < 7:
                        message = "Running"
                    elif printer_state == 9:
                        message = "Complete"
                    elif printer_state == 100:
                        message = "check slap switch"
                    resp_485(message=message)
                    print(message)
                elif master_command[1] == 't':         # turnoff all motors
                    off_motor()
                    run_motor_flag = False
                    current_silo = 0
                    message = "OK"
                    resp_485(message=message)
                elif master_command[1] == 'd':          # turn on debug
                    if len(master_command)>= 3:
                        message = "Debug "
                        # ==== debug_command ======
                        if master_command[2] == '1':                        #  '3d1\n' run roller motor forward 1 second
                            debug_roller_motor_forward = True
                            paper_test_flag = False
                            message = message + "roller forward"
                            debugging_state = 0
                        elif master_command[2] == '2':                      #  '3d2\n' run roller motor backward 1 second
                            debug_roller_motor_backward = True
                            paper_test_flag = False
                            message = message + "roller backward"
                            debugging_state = 0
                        elif master_command[2] == '3':                      #  '3d3\n' run slap motor forward 0.1 second
                            debug_slap_motor_forward = True
                            message = message + "slap forward"
                            debugging_state = 0
                        elif master_command[2] == '4':                      #  '3d4\n' run slap motor backward 0.1 second
                            debug_slap_motor_backward = True
                            message = message + "slap backward"
                            debugging_state = 0
                        elif master_command[2] == '5':
                            On_slab()
                            message = "On slab"
                        elif master_command[2] == '6':
                            Off_slab()
                            message = "Off slab"
                        elif master_command[2] == '7':
                            On_roller()
                            message = "On roller"
                        elif master_command[2] == '8':
                            Off_roller()
                            message = "Off roller"                            
                        resp_485(message=message)
                elif master_command[1] == 'u':          # update params
                    message = "Update parameters"
                    try:
                        params_file = open (parameter_file_name, "w")
                        params_file.write(master_command[2:])
                        params_file.close()
                    except:
                        message = "Update fail"
                    resp_485(message=message)
                elif master_command[1] == 'o':
                    message = "message: "
                    try:
                        params_file = open (parameter_file_name, "r")
                        message = params_file.read()
                        params_file.close()
                    except:
                        message = "read file error!"
                    resp_485(message=message)

            execute_flag = False
            master_command = ""
    
    # ============ run printer state machine ========
    # previous_state = printer_state
    if printer_state == 0:
        if run_printer_flag == True:
            motor1_controller.active(0)
            motor2_controller.active(0)
            printer_state = 1
            printer_state_timer = time.ticks_ms()
            set_slap_motor_up()
            set_roller_motor_forward()
            run_printer_flag = False
    elif printer_state == 1:
        On_roller()
        On_slab()
        if (time.ticks_ms() - printer_state_timer) >= 100:
            printer_state = 2
            print("state 1")
            printer_state_timer = time.ticks_ms()
            motor2_controller.active(1)
    elif printer_state == 2:                                            # slapup
        if time.ticks_ms()-printer_state_timer>= slap_up_time:
            printer_state = 3
            print("state 2")
            printer_state_timer = time.ticks_ms()
            motor1_controller.active(0)
            motor2_controller.active(0)
    elif printer_state == 3:                                            # wait for sticker
        if (time.ticks_ms() - printer_state_timer) >= on_delay:
            printer_state = 4
            print("state 3")
            motor1_controller.active(1)
            printer_state_timer = time.ticks_ms()
    elif printer_state == 4:                                            # === rolling paper
        if time.ticks_ms() - printer_state_timer >= 5000:               # === if switch not pressed within 5 seconds >> goto state 100
            printer_state = 100
            print("state 100")
            motor1_controller.active(0)
            motor2_controller.active(0)
        else:
            if duo_switch.value() == 1 or time.ticks_ms() - printer_state_timer >= 2500:
                print("state 4")
                printer_state = 44
                printer_state_timer = time.ticks_ms()
                #motor1_controller.active(0)
                motor2_controller.active(0)
                set_slap_motor_down()
                set_roller_motor_forward()
    elif printer_state == 44:
        if time.ticks_ms() - printer_state_timer >= 50:
            printer_state_timer = time.ticks_ms()
            motor1_controller.active(0)
            printer_state = 5            
    elif printer_state == 5:
        if time.ticks_ms() - printer_state_timer >= 300:
            printer_state_timer = time.ticks_ms()
            motor1_controller.active(1)
            print("state 5")
            printer_state = 6
    elif printer_state == 6:
        if time.ticks_ms() - printer_state_timer >= 30:
            printer_state_timer = time.ticks_ms()
            motor1_controller.active(0)
            motor2_controller.active(0)
            print("state 6")
            printer_state = 7
    elif printer_state == 7:                                            # wait rolling more time     
        if time.ticks_ms() - printer_state_timer >= 130:
            printer_state = 8
            print("state 7")
            motor1_controller.active(0)
            motor2_controller.active(1)
            printer_state_timer = time.ticks_ms()
    elif printer_state == 8:
        if time.ticks_ms()-printer_state_timer>=slap_down_time:          # slap down
            printer_state = 9
            print("state 8")
            motor1_controller.active(0)
            motor2_controller.active(0)
            Off_slab()
            paper_test_flag = True
            #Off_roller()
    elif printer_state == 9:
        pass
    elif printer_state == 100:
        pass

    if debug_roller_motor_forward:
        if debugging_state == 0:
            On_roller()
            set_roller_motor_forward()
            motor1_controller.active(1)
            debugging_timer = time.ticks_ms()
            debugging_state = 1
        elif debugging_state == 1:
            if time.ticks_ms() - debugging_timer >= 500:
                motor1_controller.active(0)
                Off_roller()
                debugging_state = 2
                debug_roller_motor_forward = False
        elif debugging_state == 2:
            pass
    
    if debug_roller_motor_backward:
        if debugging_state == 0:
            On_roller()
            set_roller_motor_backward()
            motor1_controller.active(1)
            debugging_state = 1
            debugging_timer = time.ticks_ms()
        elif debugging_state == 1:
            if time.ticks_ms() - debugging_timer >= 50: ###
                motor1_controller.active(0)
                Off_roller()
                debugging_state = 2
                debug_roller_motor_backward = False
        elif debugging_state == 2:
            pass
    
    if debug_slap_motor_forward:
        if debugging_state == 0:
            set_slap_motor_up()
            On_slab()
            motor2_controller.active(1)
            debugging_state = 1
            debugging_timer = time.ticks_ms()
        elif debugging_state == 1:
            if time.ticks_ms() - debugging_timer >= 50:
                motor2_controller.active(0)
                Off_slab()
                debugging_state = 2
                debug_slap_motor_forward = False
        elif debugging_state == 2:
            pass
    
    if debug_slap_motor_backward:
        if debugging_state == 0:
            set_slap_motor_down()
            On_slab()
            motor2_controller.active(1)
            debugging_state = 1
            debugging_timer = time.ticks_ms()
        elif debugging_state == 1:
            if time.ticks_ms() - debugging_timer >= 50:
                motor2_controller.active(0)
                Off_slab()
                debug_slap_motor_backward = False
                debugging_state = 2
        elif debugging_state == 2:
            pass


    if origin_state == 0:
        if origin_flag == True:
            On_roller()
            On_slab()
            motor1_controller.active(0)
            motor2_controller.active(0)
            set_roller_motor_backward()
            set_slap_motor_down()
            origin_state_timer = time.ticks_ms()
            origin_state = False
            paper_test_flag = False
            origin_state = 1
    elif origin_state == 1:
        if time.ticks_ms() - origin_state_timer >= 5:
            motor1_controller.active(1)
            motor2_controller.active(1)
            origin_state_timer = time.ticks_ms()
            origin_state = 2
    elif origin_state == 2:
        if time.ticks_ms() - origin_state_timer >= 200:
            origin_state = 5
            motor2_controller.active(0)
        if slap_switch.value() == 0:
            origin_state = 3
            motor2_controller.active(0)
            Off_slab()
            origin_state_timer = time.ticks_ms()
    elif origin_state == 3:
        if time.ticks_ms() - origin_state_timer >= 100:
            motor1_controller.active(0)
            Off_roller()
            #Off_slab()
            origin_state = 4
            paper_test_flag = True
    elif origin_state == 4:
        pass
    elif origin_state == 5:     # slap switch error
        paper_test_flag = True

    # if previous_state != printer_state:
    #    resp_485(str(printer_state))

        


