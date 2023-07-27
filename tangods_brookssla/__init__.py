from .BrooksSLA import BrooksSLA


def main():
    import sys
    import tango.server

    args = ["BrooksSLA"] + sys.argv[1:]
    tango.server.run((BrooksSLA,), args=args)
