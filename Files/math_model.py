import math
import csv
import sys
import traceback

try:

    class Constants:
        DT = 0.1
        TOTAL_TIME = 600
        G = 6.6743e-11
        g0 = 9.81
        KERBIN_MASS = 5.2915158e+22
        KERBIN_RADIUS = 600000
        KERBIN_ROTATION_PERIOD = 21549.425
        ROTATION_SPEED = 2 * math.pi / KERBIN_ROTATION_PERIOD
        ATMOSPHERE_HEIGHT = 70000
        P0 = 101325
        H_SCALE = 5600
        TARGET_APOAPSIS = 200000

    class Engine:

        def __init__(self, name, dry, fuel, thrust_asl, thrust_vac,
            isp_asl, isp_vac):
            self.name = name
            self.dry_mass = dry
            self.fuel_mass = fuel
            self.thrust_asl = thrust_asl
            self.thrust_vac = thrust_vac
            self.isp_asl = isp_asl
            self.isp_vac = isp_vac

    class Rocket:

        def __init__(self):
            self.t = 0
            self.position = [Constants.KERBIN_RADIUS, 0, 0]
            surf_speed = Constants.KERBIN_RADIUS * Constants.ROTATION_SPEED
            self.velocity = [0, 0, surf_speed]
            self.throttle = 1.0
            self.pitch = 90.0
            self.phase = 'PHASE1_ASCENT'
            self.stage1 = Engine('Stage1', dry=26093, fuel=122000,
                thrust_asl=2800000, thrust_vac=3500000, isp_asl=250,
                isp_vac=280)
            self.stage2 = Engine('Stage2', dry=7000, fuel=40000,
                thrust_asl=1300000, thrust_vac=1300000, isp_asl=280,
                isp_vac=320)
            self.stage3 = Engine('Stage3', 1000, 4000, 300000, 3000000,
                100, 345)
            self.payload = 9200
            self.stages = [self.stage1, self.stage2, self.stage3]
            self.current_stage_idx = 0

        @property
        def current_engine(self):
            if self.current_stage_idx < len(self.stages):
                return self.stages[self.current_stage_idx]
            return None

        def get_mass(self):
            m = self.payload
            for i in range(self.current_stage_idx, len(self.stages)):
                eng = self.stages[i]
                m += eng.dry_mass + eng.fuel_mass
            return m

        def get_atmosphere(self, alt):
            if alt > Constants.ATMOSPHERE_HEIGHT:
                return (0, 0)
            p = Constants.P0 * math.exp(-alt / Constants.H_SCALE)
            d = 1.225 * math.exp(-alt / Constants.H_SCALE)
            return (p, d)

        def update_physics(self, dt):
            r_vec = self.position
            r = math.sqrt(sum(x ** 2 for x in r_vec))
            alt = r - Constants.KERBIN_RADIUS
            g_acc = [-(Constants.G * Constants.KERBIN_MASS / r ** 3) * x for
                x in r_vec]
            (pres, rho) = self.get_atmosphere(alt)
            v_vec = self.velocity
            atm_vel = [-r_vec[2] * Constants.ROTATION_SPEED, 0, r_vec[0] *
                Constants.ROTATION_SPEED]
            air_vel = [v - a for (v, a) in zip(v_vec, atm_vel)]
            air_spd = math.sqrt(sum(x ** 2 for x in air_vel))
            mass = self.get_mass()
            drag_acc = [0, 0, 0]
            if air_spd > 0.1:
                drag_F = 0.5 * rho * air_spd ** 2 * 0.5 * 75.0
                drag_acc = [-(drag_F / mass) * (v / air_spd) for v in air_vel]
            thrust_val = 0
            eng = self.current_engine
            if eng and self.throttle > 0 and eng.fuel_mass > 0:
                vac_k = max(0, 1 - pres / Constants.P0)
                th = eng.thrust_asl + (eng.thrust_vac - eng.thrust_asl) * vac_k
                th *= self.throttle
                thrust_val = th
                isp = eng.isp_asl + (eng.isp_vac - eng.isp_asl) * vac_k
                dm = th / (isp * Constants.g0) * dt
                eng.fuel_mass -= dm
                if eng.fuel_mass < 0:
                    eng.fuel_mass = 0
            up = [x / r for x in r_vec]
            east = [0, 0, 1]
            rad_pitch = math.radians(self.pitch)
            th_dir = [up[i] * math.sin(rad_pitch) + east[i] * math.cos(
                rad_pitch) for i in range(3)]
            l_th = math.sqrt(sum(x ** 2 for x in th_dir))
            if l_th > 0:
                th_dir = [x / l_th for x in th_dir]
            thrust_acc = [thrust_val / mass * x for x in th_dir]
            total_acc = [g + d + t for (g, d, t) in zip(g_acc, drag_acc,
                thrust_acc)]
            self.velocity = [v + a * dt for (v, a) in zip(self.velocity,
                total_acc)]
            self.position = [p + v * dt for (p, v) in zip(self.position,
                self.velocity)]
            self.t += dt
            return thrust_val

        def get_orbit(self):
            try:
                r = math.sqrt(sum(x ** 2 for x in self.position))
                v = math.sqrt(sum(x ** 2 for x in self.velocity))
                mu = Constants.G * Constants.KERBIN_MASS
                en = v ** 2 / 2 - mu / r
                if en >= -0.1:
                    return (r - Constants.KERBIN_RADIUS, r - Constants.
                        KERBIN_RADIUS)
                a = -mu / (2 * en)
                r_vec = self.position
                v_vec = self.velocity
                rv_dot = sum(x * y for (x, y) in zip(r_vec, v_vec))
                e_vec = [((v ** 2 - mu / r) * r_vec[i] - rv_dot * v_vec[i]) /
                    mu for i in range(3)]
                e_sq = sum(x ** 2 for x in e_vec)
                if e_sq < 0:
                    e_sq = 0
                e = math.sqrt(e_sq)
                apo = a * (1 + e) - Constants.KERBIN_RADIUS
                peri = a * (1 - e) - Constants.KERBIN_RADIUS
                return (apo, peri)
            except Exception:
                return (0, 0)

        def autopilot(self):
            r = math.sqrt(sum(x ** 2 for x in self.position))
            alt = r - Constants.KERBIN_RADIUS
            (apo, peri) = self.get_orbit()
            eng = self.current_engine
            r_vec = self.position
            v_vec = self.velocity
            v_vert = sum(x * y for (x, y) in zip(r_vec, v_vec)) / r
            if self.phase == 'PHASE1_ASCENT':
                if alt < 2000 or v_vert < 50:
                    self.throttle = 0.8
                else:
                    self.throttle = 0.78
                if alt < 30000:
                    safe_alt = max(0, alt)
                    ratio = safe_alt / 30000.0
                    self.pitch = 90 - 48 * ratio ** 0.45
                else:
                    self.pitch = 50
                if eng.fuel_mass <= 0:
                    self.current_stage_idx = 1
                    self.phase = 'PHASE2_CENTER'
            elif self.phase == 'PHASE2_CENTER':
                self.pitch = 56
                self.throttle = 1.0
                if apo > Constants.TARGET_APOAPSIS:
                    self.throttle = 0
                    self.current_stage_idx = 2
                    self.phase = 'PHASE3_COAST'
                elif eng.fuel_mass <= 0:
                    self.current_stage_idx = 2
            elif self.phase == 'PHASE3_COAST':
                self.throttle = 0
                self.pitch = 0
                if Constants.TARGET_APOAPSIS - alt < 3000 or v_vert < 20 and alt > 70000:
                    self.phase = 'PHASE3_CIRC'
            elif self.phase == 'PHASE3_CIRC':
                self.throttle = 1.0
                self.pitch = 0
                if peri > Constants.TARGET_APOAPSIS - 5000 or eng.fuel_mass <= 0:
                    self.throttle = 0
                    self.phase = 'ORBIT'

    def main():
        print('Запуск main()...')
        rocket = Rocket()
        with open('mission_data.csv', 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['time', 'altitude', 'apoapsis', 'periapsis',
                'speed', 'mass', 'thrust', 'stage', 'phase'])
            steps = int(Constants.TOTAL_TIME / Constants.DT)
            print(f'Всего шагов: {steps}')
            for i in range(steps):
                try:
                    rocket.autopilot()
                    th = rocket.update_physics(Constants.DT)
                    if i % 10 == 0:
                        r_vec = rocket.position
                        r = math.sqrt(sum(x ** 2 for x in r_vec))
                        atm_vel = [-r_vec[2] * Constants.
                            ROTATION_SPEED, 0, r_vec[0] * Constants.
                            ROTATION_SPEED]
                        surf_v_vec = [v - a for (v, a) in zip(rocket.
                            velocity, atm_vel)]
                        surf_speed = math.sqrt(sum(x ** 2 for x in
                            surf_v_vec))
                        m = rocket.get_mass()
                        (apo, peri) = rocket.get_orbit()
                        w.writerow([f'{rocket.t:.2f}',
                            f'{r - Constants.KERBIN_RADIUS:.2f}',
                            f'{apo:.2f}', f'{peri:.2f}',
                            f'{surf_speed:.2f}', f'{m:.2f}',
                            f'{th:.2f}', rocket.current_stage_idx, rocket.
                            phase])
                    if i % 1000 == 0:
                        print(f'Шаг {i}, T={rocket.t:.1f}')
                except Exception as e:
                    print(f'КРИТИЧЕСКАЯ ОШИБКА НА ШАГЕ {i}: {e}')
                    traceback.print_exc()
                    break
        print('Завершено успешно.')
    if __name__ == '__main__':
        main()
except Exception as global_e:
    print(f'ОШИБКА ИНИЦИАЛИЗАЦИИ: {global_e}')
    traceback.print_exc()
