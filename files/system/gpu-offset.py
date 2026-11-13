#!/usr/bin/env python3
"""Селестия: сдвиг кривой частоты RTX 3060 через NVML (андервольт по сути вместе с лимитом 120 Вт).
  sudo python3 -I gpu-offset.py show
  sudo python3 -I gpu-offset.py set GPC_MHZ [MEM_MHZ]     (0 0 = как с завода; сбрасывается при перезагрузке)"""
import sys
import pynvml as n
n.nvmlInit(); h = n.nvmlDeviceGetHandleByIndex(0)
def show():
    print(f"core {n.nvmlDeviceGetGpcClkVfOffset(h):+d} MHz, mem {n.nvmlDeviceGetMemClkVfOffset(h):+d} MHz, "
          f"limit {n.nvmlDeviceGetEnforcedPowerLimit(h)/1000:.0f} W")
cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
if cmd == "set":
    gpc = int(sys.argv[2]); mem = int(sys.argv[3]) if len(sys.argv) > 3 else n.nvmlDeviceGetMemClkVfOffset(h)
    if not (-200 <= gpc <= 300 and -500 <= mem <= 1500):
        sys.exit("вне безопасного диапазона Селестии: core -200..300, mem -500..1500")
    n.nvmlDeviceSetGpcClkVfOffset(h, gpc)
    n.nvmlDeviceSetMemClkVfOffset(h, mem)
show()
