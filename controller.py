import pygame
import time
import socketio

ROVER_IP = "VUL_HIER_HET_IP_ADRES_IN"

pygame.init()
pygame.joystick.init()

controller = pygame.joystick.Joystick(0)
controller.init()

sio = socketio.Client()
sio.connect(f"http://{ROVER_IP}:5000", namespaces=["/json"])

chassis_lamp_aan = False
chassis_pwm = 0
camera_lamp_aan = False
camera_pwm = 0

lamp_commando = {"T": 132, "IO4": chassis_pwm, "IO5": camera_pwm}
sio.emit("json", lamp_commando, namespace="/json")

snelheid = 0.5

hoek_horizon = 0.0
hoek_verticaal = 0.0

running = True


def deadzone(waarde):
    if abs(waarde) < 0.05:
        return 0.0
    return waarde


def begrens(waarde):
    return max(-1.0, min(1.0, waarde))


def maximaal(waarde):
    return max(0.0, min(1.3, waarde))


def max_horizon(waarde):
    return max(-180, min(180, waarde))


def max_verticaal(waarde):
    return max(-30, min(90, waarde))


try:
    while running:
        for event in pygame.event.get():
            # buttons
            if event.type == pygame.JOYBUTTONDOWN:

                # afsluiten
                if event.button == 7:
                    running = False

                # chassislamp
                if event.button == 0:
                    chassis_lamp_aan = not chassis_lamp_aan
                    if chassis_lamp_aan == True:
                        chassis_pwm = 255
                        lamp_commando = {
                            "T": 132,
                            "IO4": chassis_pwm,
                            "IO5": camera_pwm,
                        }
                        sio.emit("json", lamp_commando, namespace="/json")

                    else:
                        chassis_pwm = 0
                        lamp_commando = {
                            "T": 132,
                            "IO4": chassis_pwm,
                            "IO5": camera_pwm,
                        }
                        sio.emit("json", lamp_commando, namespace="/json")

                # cameralamp
                if event.button == 1:
                    camera_lamp_aan = not camera_lamp_aan
                    if camera_lamp_aan == True:
                        camera_pwm = 255
                        lamp_commando = {
                            "T": 132,
                            "IO4": chassis_pwm,
                            "IO5": camera_pwm,
                        }
                        sio.emit("json", lamp_commando, namespace="/json")

                    else:
                        camera_pwm = 0
                        lamp_commando = {
                            "T": 132,
                            "IO4": chassis_pwm,
                            "IO5": camera_pwm,
                        }
                        sio.emit("json", lamp_commando, namespace="/json")

                # snelheid verlagen
                if event.button == 4:
                    snelheid = maximaal(snelheid - 0.1)

                    print("snelheid:", round(snelheid, 1))

                # snelheid verhogen
                if event.button == 5:
                    snelheid = maximaal(snelheid + 0.1)

                    print("snelheid:", round(snelheid, 1))

        # gimbal
        gimbal_x = deadzone(controller.get_axis(2))  # rechter joystick links/rechts
        gimbal_y = deadzone(controller.get_axis(3))  # rechter joystick boven/onder

        if gimbal_x != 0 or gimbal_y != 0:
            hoek_horizon += gimbal_x * 5
            hoek_horizon = max_horizon(hoek_horizon)

            hoek_verticaal += -gimbal_y * 5
            hoek_verticaal = max_verticaal(hoek_verticaal)

            gimbal_commando = {
                "T": 133,
                "X": hoek_horizon,
                "Y": hoek_verticaal,
                "SPD": 0,
                "ACC": 0,
            }

            sio.emit("json", gimbal_commando, namespace="/json")

        # rijden/sturen
        sturen = deadzone(controller.get_axis(0))  # linker joystick links/rechts
        rijden = deadzone(controller.get_axis(1))  # linker joystick boven/onder

        links = -rijden + sturen
        rechts = -rijden - sturen

        input_links = begrens(links) * snelheid
        input_rechts = begrens(rechts) * snelheid

        rijden_commando = {"T": 1, "L": input_links, "R": input_rechts}

        sio.emit("json", rijden_commando, namespace="/json")

        time.sleep(0.1)

finally:
    stop_commando = {"T": 1, "L": 0, "R": 0}
    sio.emit("json", stop_commando, namespace="/json")

    gimbal_midden = {
        "T": 133,
        "X": 0,
        "Y": 0,
        "SPD": 0,
        "ACC": 0,
    }
    sio.emit("json", gimbal_midden, namespace="/json")

    stop_lamp_commando = {
        "T": 132,
        "IO4": 0,
        "IO5": 0,
    }
    sio.emit("json", stop_lamp_commando, namespace="/json")

    time.sleep(1.0)

    sio.disconnect()
    pygame.quit()
