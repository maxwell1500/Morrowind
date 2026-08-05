import sys, importlib.util
spec = importlib.util.spec_from_file_location("gen", r'C:\Users\max\Projects\Morrowind\scripts\generate_esp_full.py')
mod = importlib.util.module_from_spec(spec)
mod.EXTERIOR_REFR_LIMIT = 100
spec.loader.exec_module(mod)
mod.main()
