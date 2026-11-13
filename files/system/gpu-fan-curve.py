#!/usr/bin/env python3
"""Селестия: вентиляторы RTX 3060 не ниже 50 %, пока карта тёплая (2026-11-06).

Завод держит вентиляторы на 0 до ~60 °C, и на столе карта ходит качелями 50-60 °C. Тест 06.11:
ровные 50 % дают 37-38 °C при тех же ~23 Вт, на слух не слышно. 30 % карта не запускает, 40 % рывками.

  HOLD  ручной режим, ровно 50 %
  AUTO  заводская кривая карты (игры, и холодная карта с вентиляторами на 0)

  gpu-fan-curve.py run      сервис: раз в 3 с смотрит карту; выходя, отдаёт управление карте
  gpu-fan-curve.py auto     вернуть заводское управление (ExecStopPost)
  gpu-fan-curve.py status   что сейчас и что сервис сделал бы (только чтение, без root)

Частоты, лимит мощности и андервольт не трогает: только вентиляторы.
"""
import signal
import sys
import time

SPEED = 50          # % : ниже карта не крутит ровно
ON_AT = 35          # °C: теплее — вентиляторы нужны
OFF_AT = 32         # °C: холоднее — пусть стоят (зазор, чтобы не щёлкали на границе)
GIVE_AT = 65        # °C: отсюда управление у карты; на 60-62 она только стартует
TAKE_BELOW = 58     # °C: ниже всегда берём обратно
TAKE_FAN = 45       # %: в авто обороты ниже этого — карта их сбрасывает, берём обратно (показания дрожат у 50)
SETTLE = 15         # с: после отдачи карте дать вентиляторам раскрутиться
TICK = 3            # с
FAILS_TO_QUIT = 5   # подряд ошибок NVML: выйти, systemd перезапустит, ExecStopPost отдаст авто

HOLD, AUTO = "hold", "auto"


def decide(state, temp, fan, since):
    """Новое состояние. temp °C, fan — наименьшие обороты сейчас, %, since — секунд в этом состоянии."""
    if temp >= GIVE_AT or temp <= OFF_AT:
        return AUTO
    if temp >= ON_AT and temp < TAKE_BELOW:
        return HOLD
    if temp >= TAKE_BELOW and state == AUTO and fan < TAKE_FAN and since >= SETTLE:
        return HOLD     # после игры карта сбросила обороты в 58-64 °C: тут она бы и застряла
    return state        # 33-34 °C и 58-64 °C с крутящимися: как есть


class Card:
    def __init__(self):
        import pynvml
        self.n = pynvml
        self.n.nvmlInit()
        self.h = self.n.nvmlDeviceGetHandleByIndex(0)
        self.fans = self.n.nvmlDeviceGetNumFans(self.h)

    def temp(self):
        return self.n.nvmlDeviceGetTemperature(self.h, 0)

    def fan(self):
        return min(self.n.nvmlDeviceGetFanSpeed_v2(self.h, i) for i in range(self.fans))

    def holding(self):
        """Ручной режим и наша цель на всех вентиляторах? После сна драйвер мог это сбросить."""
        return all(self.n.nvmlDeviceGetFanControlPolicy_v2(self.h, i) == 1
                   and self.n.nvmlDeviceGetTargetFanSpeed(self.h, i) == SPEED for i in range(self.fans))

    def hold(self):
        for i in range(self.fans):
            self.n.nvmlDeviceSetFanControlPolicy(self.h, i, 1)
            self.n.nvmlDeviceSetFanSpeed_v2(self.h, i, SPEED)

    def auto(self):
        for i in range(self.fans):
            self.n.nvmlDeviceSetFanControlPolicy(self.h, i, 0)
            self.n.nvmlDeviceSetDefaultFanSpeed_v2(self.h, i)


def run(card, clock=time.monotonic, sleep=time.sleep, say=print, ticks=None):
    state, since, fails = AUTO, clock(), 0
    card.auto()
    say("start: авто", flush=True)
    while ticks is None or ticks > 0:
        if ticks is not None:
            ticks -= 1
        try:
            temp, fan = card.temp(), card.fan()
            new = decide(state, temp, fan, clock() - since)
            if new != state:
                say(f"{temp} °C, обороты {fan} %: {state} → {new}", flush=True)
                state, since = new, clock()
                card.hold() if state == HOLD else card.auto()
            elif state == HOLD and not card.holding():
                say(f"{temp} °C: настройку сбросили, ставлю снова", flush=True)
                card.hold()
            fails = 0
        except Exception as e:      # карта занята, просыпается, драйвер перезагружается
            fails += 1
            say(f"NVML: {e} ({fails}/{FAILS_TO_QUIT})", flush=True)
            if fails >= FAILS_TO_QUIT:
                sys.exit(1)
        sleep(TICK)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    card = Card()
    if cmd == "auto":
        card.auto()
    elif cmd == "status":
        pol = [card.n.nvmlDeviceGetFanControlPolicy_v2(card.h, i) for i in range(card.fans)]
        now = HOLD if all(p == 1 for p in pol) else AUTO
        t, f = card.temp(), card.fan()
        print(f"{t} °C, обороты {f} %, сейчас {now}, сервис хотел бы {decide(now, t, f, SETTLE)}")
    elif cmd == "run":
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: sys.exit(0))
        try:
            run(card)
        finally:
            card.auto()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
