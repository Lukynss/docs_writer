from setuptools import setup

APP = ["docs_writer.py"]

OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "Docs Writer",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": False,
        "NSAppleEventsUsageDescription": (
            "Docs Writer needs accessibility access to simulate keyboard input."
        ),
    },
    "packages": ["pynput"],
}

setup(
    app=APP,
    name="Docs Writer",
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
