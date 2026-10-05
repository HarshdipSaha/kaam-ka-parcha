INTAKE_T = "front brake pad ₹450, labour ₹200, Somvaar shaam tak"
INTAKE_V = "front brake pad saade chaar sau labour do sau Somvaar shaam tak"


class ScriptedPrisma:
    """Fake Prisma returning scripted outputs in call order; an Exception entry is raised instead."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def transcribe(self, wav, *, mode, bias=None, score=1.0):
        self.calls.append((wav, mode, bias, score))
        if not self.script:
            raise AssertionError(f"unexpected extra Prisma call (mode={mode})")
        out = self.script.pop(0)
        if isinstance(out, Exception):
            raise out
        return out
